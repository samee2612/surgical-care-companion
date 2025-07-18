"""
Conversations API Endpoints
Handles conversation data and management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database.connection import get_db
from models import VoiceInteraction as Conversation, ConversationMessage
from models.patient import Patient

router = APIRouter()

@router.get("/conversations", response_model=List[dict])
async def get_conversations(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    urgency_level: Optional[str] = Query(default=None),
    patient_id: Optional[str] = Query(default=None)
):
    """
    Get conversations with optional filtering
    """
    try:
        query = db.query(Conversation).join(Patient)
        
        if urgency_level:
            query = query.filter(Conversation.urgency_level == urgency_level)
        
        if patient_id:
            query = query.filter(Conversation.patient_id == patient_id)
        
        conversations = query.order_by(Conversation.started_at.desc()).offset(offset).limit(limit).all()
        
        result = []
        for conv in conversations:
            result.append({
                "id": conv.id,
                "patient_id": conv.patient_id,
                "patient_name": conv.patient.full_name if conv.patient else "Unknown",
                "phone_number": conv.phone_number,
                "call_status": conv.call_status,
                "call_duration": conv.call_duration,
                "intent": conv.intent,
                "sentiment": conv.sentiment,
                "urgency_level": conv.urgency_level,
                "pain_level": conv.pain_level,
                "symptoms": conv.symptoms or [],
                "concerns": conv.concerns or [],
                "actions_required": conv.actions_required or [],
                "started_at": conv.started_at.isoformat() if conv.started_at else None,
                "ended_at": conv.ended_at.isoformat() if conv.ended_at else None,
                "transcript": conv.transcript,
                "conversation_json": conv.conversation_json or {"messages": []}
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conversations: {str(e)}")

@router.get("/conversations/{conversation_id}", response_model=dict)
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """
    Get a specific conversation by ID
    """
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "id": conversation.id,
            "patient_id": conversation.patient_id,
            "patient_name": conversation.patient.full_name if conversation.patient else "Unknown",
            "phone_number": conversation.phone_number,
            "call_sid": conversation.call_sid,
            "call_direction": conversation.call_direction,
            "call_status": conversation.call_status,
            "call_duration": conversation.call_duration,
            "conversation_json": conversation.conversation_json or {"messages": []},
            "transcript": conversation.transcript,
            "intent": conversation.intent,
            "entities": conversation.entities or {},
            "sentiment": conversation.sentiment,
            "urgency_level": conversation.urgency_level,
            "symptoms": conversation.symptoms or [],
            "pain_level": conversation.pain_level,
            "concerns": conversation.concerns or [],
            "actions_required": conversation.actions_required or [],
            "started_at": conversation.started_at.isoformat() if conversation.started_at else None,
            "ended_at": conversation.ended_at.isoformat() if conversation.ended_at else None,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conversation: {str(e)}")

@router.get("/conversations/stats", response_model=dict)
async def get_conversation_stats(
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get conversation statistics
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total conversations
        total_conversations = db.query(Conversation).filter(
            Conversation.started_at >= cutoff_date
        ).count()
        
        # Urgent conversations
        urgent_conversations = db.query(Conversation).filter(
            Conversation.started_at >= cutoff_date,
            Conversation.urgency_level.in_(['critical', 'high'])
        ).count()
        
        # Completed conversations
        completed_conversations = db.query(Conversation).filter(
            Conversation.started_at >= cutoff_date,
            Conversation.call_status == 'completed'
        ).count()
        
        # Average pain level
        pain_levels = db.query(Conversation.pain_level).filter(
            Conversation.started_at >= cutoff_date,
            Conversation.pain_level.isnot(None)
        ).all()
        
        avg_pain_level = None
        if pain_levels:
            avg_pain_level = sum(p[0] for p in pain_levels) / len(pain_levels)
        
        # Sentiment distribution
        sentiment_counts = db.query(Conversation.sentiment, db.func.count(Conversation.sentiment)).filter(
            Conversation.started_at >= cutoff_date,
            Conversation.sentiment.isnot(None)
        ).group_by(Conversation.sentiment).all()
        
        sentiment_distribution = {sentiment: count for sentiment, count in sentiment_counts}
        
        return {
            "total_conversations": total_conversations,
            "urgent_conversations": urgent_conversations,
            "completed_conversations": completed_conversations,
            "avg_pain_level": round(avg_pain_level, 1) if avg_pain_level else None,
            "sentiment_distribution": sentiment_distribution,
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@router.post("/conversations/{conversation_id}/actions", response_model=dict)
async def mark_actions_completed(
    conversation_id: str,
    actions: List[str],
    db: Session = Depends(get_db)
):
    """
    Mark specific actions as completed for a conversation
    """
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Update the conversation with completed actions
        if not conversation.conversation_json:
            conversation.conversation_json = {"messages": []}
        
        if "completed_actions" not in conversation.conversation_json:
            conversation.conversation_json["completed_actions"] = []
        
        conversation.conversation_json["completed_actions"].extend(actions)
        
        # Add a system message about completed actions
        conversation.conversation_json["messages"].append({
            "role": "system",
            "content": f"Actions completed: {', '.join(actions)}",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "action_completion"
        })
        
        db.commit()
        
        return {"message": "Actions marked as completed", "completed_actions": actions}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating actions: {str(e)}")
