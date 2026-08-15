"""
API endpoints for chat-based troubleshooting.
"""
from fastapi import APIRouter, HTTPException, Depends
import logging
import sys
from pathlib import Path
from typing import Optional, List
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pydantic import BaseModel
from app.services.semantic_validator import get_semantic_validator
from app.services.indexer import get_indexer
from app.services.retriever import get_retriever
from app.services.llm import get_llm_service
from app.services.session_store import get_session_store
from app.auth.dependencies import get_current_user
from app.auth.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatStartRequest(BaseModel):
    """Request to start a new chat session."""
    manual_id: str
    question: str


class ChatMessageRequest(BaseModel):
    """Request to send a message in existing session."""
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    session_id: str
    answer: str
    steps: Optional[List[str]] = None
    context_used: Optional[List[str]] = None
    references: Optional[str] = None
    response_time_ms: Optional[int] = None


@router.post("/chat/start", response_model=ChatResponse)
async def start_chat(request: ChatStartRequest, current_user: User = Depends(get_current_user)):
    """
    Start a new chat session.
    
    Workflow:
    1. Validate intent
    2. Check manual exists
    3. Retrieve context
    4. Generate structured answer with steps
    5. Create session
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Starting chat for manual: {request.manual_id} (user: {current_user.username})")
        
        # Step 1: Validate intent
        validator = get_semantic_validator()
        is_valid, error_message = validator.validate(request.question)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Step 2: Check manual
        indexer = get_indexer()
        if not indexer.is_indexed(request.manual_id):
            raise HTTPException(
                status_code=404,
                detail=f"Manual '{request.manual_id}' is not indexed"
            )
        
        # Step 3: Retrieve context
        retriever = get_retriever()
        context_chunks = retriever.retrieve(request.manual_id, request.question)
        
        if not context_chunks:
            raise HTTPException(
                status_code=404,
                detail="No relevant information found in the manual"
            )
        
        logger.info(f"Retrieved {len(context_chunks)} context chunks")
        
        # Step 4: Generate structured answer
        llm_service = get_llm_service()
        
        # Enhanced prompt for structured output
        structured_prompt = _build_structured_prompt(request.question, context_chunks)
        
        answer = await llm_service.generate_response(
            question=structured_prompt,
            context_chunks=[],  # Already embedded in prompt
            manual_id=request.manual_id,
            is_validation=True  # Use direct prompt
        )
        
        # Parse steps from answer
        steps = _parse_steps(answer)
        
        # Step 5: Create session
        session_store = get_session_store()
        session_id = session_store.create_session(
            manual_id=request.manual_id,
            question=request.question,
            answer=answer,
            context_chunks=context_chunks,
            steps=steps
        )
        
        logger.info(f"Chat session created: {session_id}")
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Extract page numbers from context chunks
        page_numbers = set()
        for chunk in context_chunks:
            # Look for [Page X] markers at start of chunks
            import re
            # Match [Page X] or [Page X] patterns
            pages = re.findall(r'\[Page (\d+)\]', chunk, re.IGNORECASE)
            page_numbers.update(pages)
        
        # Generate references footer with page numbers
        if page_numbers:
            sorted_pages = sorted([int(p) for p in page_numbers])
            if len(sorted_pages) > 5:
                page_range = f"Pages {sorted_pages[0]}-{sorted_pages[-1]}"
            else:
                page_range = f"Page{'s' if len(sorted_pages) > 1 else ''} {', '.join(map(str, sorted_pages))}"
            references = f"📚 {request.manual_id.upper()} Manual | {page_range} | {len(context_chunks)} sections"
        else:
            references = f"📚 {request.manual_id.upper()} Manual | {len(context_chunks)} sections"
        
        return ChatResponse(
            session_id=session_id,
            answer=answer,
            steps=steps,
            context_used=context_chunks,
            references=references,
            response_time_ms=response_time_ms
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/message", response_model=ChatResponse)
async def chat_message(request: ChatMessageRequest, current_user: User = Depends(get_current_user)):
    """
    Send a follow-up message in existing session.
    
    Handles:
    - Step clarification requests
    - Alternative solution requests
    - New related questions (reuses context)
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Chat message for session: {request.session_id} (user: {current_user.username})")
        
        # Get session
        session_store = get_session_store()
        session = session_store.get_session(request.session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found or expired"
            )
        
        # Detect intent of follow-up
        message_lower = request.message.lower()
        
        # Check if asking for clarification
        step_match = re.search(r'step\s*(\d+)', message_lower)
        is_clarification = any(word in message_lower for word in ['explain', 'clarify', 'detail', 'elaborate', 'what does', 'how do'])
        is_alternative = any(word in message_lower for word in ['alternative', 'else', 'other', 'didn\'t work', 'not work', 'failed'])
        
        llm_service = get_llm_service()
        
        if is_clarification and step_match:
            # Clarify specific step - extract from the actual answer text
            step_num = int(step_match.group(1))
            
            # Extract steps from the previous answer
            previous_answer = session.answer
            step_lines = []
            for line in previous_answer.split('\n'):
                line = line.strip()
                if re.match(r'^(Step\s+)?\d+[\.\):]', line, re.IGNORECASE):
                    step_lines.append(line)
            
            if step_num > 0 and step_num <= len(step_lines):
                step_text = step_lines[step_num - 1]
                # Remove step number prefix for cleaner display
                step_text = re.sub(r'^(Step\s+)?\d+[\.\):]\s*', '', step_text, flags=re.IGNORECASE)
                
                prompt = f"""The user is troubleshooting this problem: {session.question}

They need more detail about this specific step:

**{step_text}**

Reference context from manual:
{chr(10).join(session.context_chunks[:3])}

Provide a detailed explanation including:
1. What exactly to do (step-by-step if needed)
2. What tools or parts are involved
3. What you should see/expect
4. Safety warnings if any

Format: Use clear paragraphs with bold text for important points. Keep it focused and practical."""
                
                answer = await llm_service.generate_response(
                    question=prompt,
                    context_chunks=[],
                    manual_id=session.manual_id,
                    is_validation=False
                )
            else:
                # Fallback - use general context
                prompt = f"""The user asked about "step {step_num}" from the previous answer.

Original problem: {session.question}
Previous answer: {session.answer}

User's question: {request.message}

Based on the context from the manual, provide a helpful explanation about what they're asking for.

Context from manual:
{chr(10).join(session.context_chunks[:3])}

Give a clear, practical explanation."""
                
                answer = await llm_service.generate_response(
                    question=prompt,
                    context_chunks=[],
                    manual_id=session.manual_id,
                    is_validation=False
                )
        
        elif is_alternative:
            # Suggest alternatives using same context
            prompt = f"""The user tried these troubleshooting steps but the problem persists:

Original problem: {session.question}
Steps attempted: {session.answer}

Context from manual with additional information:
{chr(10).join(session.context_chunks)}

Based on the manual, suggest:
1. Alternative procedures or checks not mentioned before
2. Other possible root causes
3. Additional diagnostic steps

Format with numbered steps. If no alternatives are documented in the manual, suggest checking other related systems mentioned in the context."""
            
            answer = await llm_service.generate_response(
                question=prompt,
                context_chunks=[],
                manual_id=session.manual_id,
                is_validation=False
            )
        
        else:
            # General follow-up - reuse context with better structure
            prompt = f"""Previous troubleshooting session:

Original problem: {session.question}
Solution provided: {session.answer}

User's follow-up question: {request.message}

Reference from manual:
{chr(10).join(session.context_chunks[:3])}

Provide a clear, helpful answer to their follow-up question. Use the manual context and previous solution to give practical guidance. Format with bullet points or numbered steps if needed."""
            
            answer = await llm_service.generate_response(
                question=prompt,
                context_chunks=[],
                manual_id=session.manual_id,
                is_validation=False
            )
        
        # Update session
        session_store.update_session(
            session_id=request.session_id,
            question=request.message,
            answer=answer
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Generate references footer
        references = f"📚 **Source:** {session.manual_id.upper()} Manual | Follow-up response"
        
        return ChatResponse(
            session_id=request.session_id,
            answer=answer,
            steps=_parse_steps(answer) if not (is_clarification or is_alternative) else None,
            context_used=None,  # Don't resend context for follow-ups
            references=references,
            response_time_ms=response_time_ms
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _build_structured_prompt(question: str, context_chunks: List[str]) -> str:
    """Build prompt that encourages structured, numbered steps."""
    context_text = "\n\n".join([f"[Section {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)])
    
    return f"""You are a maintenance troubleshooting assistant for INDUSTRIAL EQUIPMENT AND VEHICLES.

MANUAL CONTEXT:
{context_text}

USER PROBLEM: {question}

CRITICAL RULES:
- ONLY use information from the manual context above
- Do NOT make up information
- Do NOT provide recipes, cooking instructions, or unrelated content
- This is a VEHICLE/EQUIPMENT maintenance manual

INSTRUCTIONS:
1. Start with a brief ONE-LINE summary of the issue
2. Provide troubleshooting steps - EACH STEP ON A NEW LINE in this exact format:
   Step 1: First action (what to check/adjust)
   Step 2: Second action (what to verify)
   Step 3: Next action
   etc.
3. Each step must be UNIQUE - no duplicates
4. Use technical terminology from the manual
5. Keep steps concise and actionable (one sentence per step)
6. End with what to do if problem persists

IMPORTANT: Write each step on its own line starting with "Step X:" - do NOT put steps in a single paragraph.

If the information is not in the manual context, say: "This specific issue is not documented in the available manual sections."

ANSWER:"""


def _parse_steps(answer: str) -> List[str]:
    """Extract numbered steps from answer - handles multiple formats."""
    steps = []
    
    # Try 1: Match "Step X:" anywhere in text (inline or newline)
    step_pattern = r'Step\s+(\d+):\s*([^\.]+(?:\.[^\n]*?)?(?=\s*Step\s+\d+:|$))'
    matches = re.findall(step_pattern, answer, re.IGNORECASE | re.DOTALL)
    
    if matches:
        for num, text in matches:
            # Clean up the step text
            step_text = text.strip()
            # Remove trailing periods and extra whitespace
            step_text = re.sub(r'\s+', ' ', step_text)
            step_text = step_text.rstrip('.')
            if step_text and len(step_text) > 5:
                steps.append(step_text)
    
    # Try 2: If no "Step X:" found, look for numbered list "1.", "2.", etc.
    if not steps:
        lines = answer.split('\n')
        for line in lines:
            line = line.strip()
            match = re.match(r'^(\d+)[\.\)]\s*(.+)', line)
            if match:
                step_text = match.group(2).strip()
                if step_text:
                    steps.append(step_text)
    
    logger.info(f"Parsed {len(steps)} steps from answer")
    return steps
