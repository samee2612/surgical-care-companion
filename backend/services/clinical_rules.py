"""
Clinical Decision Rules Service
Business logic for clinical assessments, risk scoring, and escalation triggers.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from enum import Enum

from models import Patient, CallSession, ClinicalAlert

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    PAIN_ESCALATION = "pain_escalation"
    INFECTION_RISK = "infection_risk"
    MOBILITY_CONCERN = "mobility_concern"
    MEDICATION_ISSUE = "medication_issue"
    PSYCHOLOGICAL_DISTRESS = "psychological_distress"
    DELAYED_RECOVERY = "delayed_recovery"


class ClinicalRulesService:
    """Service for clinical decision making and risk assessment"""
    
    def __init__(self):
        self.pain_thresholds = {
            "day_1_7": {"high": 8, "critical": 9},
            "day_8_14": {"high": 7, "critical": 8},
            "day_15_30": {"high": 6, "critical": 7},
            "day_30_plus": {"high": 5, "critical": 6}
        }
        
        self.mobility_expectations = {
            "day_1": {"expected": "bed_to_chair"},
            "day_2": {"expected": "walking_with_assistance"},
            "day_7": {"expected": "walking_independently"},
            "day_14": {"expected": "stairs_with_assistance"},
            "day_30": {"expected": "normal_activities"}
        }
        
        self.logger = logger
    
    def assess_patient_risk(
        self, 
        patient: Patient, 
        call_session: CallSession,
        responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive patient risk assessment"""
        
        days_post_surgery = self._calculate_days_post_surgery(patient, call_session)
        
        # Assess different risk categories
        pain_risk = self._assess_pain_risk(responses, days_post_surgery)
        infection_risk = self._assess_infection_risk(responses, days_post_surgery)
        mobility_risk = self._assess_mobility_risk(responses, days_post_surgery)
        medication_risk = self._assess_medication_risk(responses)
        psychological_risk = self._assess_psychological_risk(responses)
        
        # Calculate overall risk
        overall_risk = self._calculate_overall_risk([
            pain_risk, infection_risk, mobility_risk, 
            medication_risk, psychological_risk
        ])
        
        # Generate alerts if needed
        alerts = self._generate_clinical_alerts(
            patient, call_session, {
                "pain": pain_risk,
                "infection": infection_risk,
                "mobility": mobility_risk,
                "medication": medication_risk,
                "psychological": psychological_risk
            }
        )
        
        return {
            "overall_risk": overall_risk,
            "risk_breakdown": {
                "pain": pain_risk,
                "infection": infection_risk,
                "mobility": mobility_risk,
                "medication": medication_risk,
                "psychological": psychological_risk
            },
            "alerts": alerts,
            "recommendations": self._generate_recommendations(overall_risk, alerts),
            "escalation_required": overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL] or len(alerts) > 0
        }
    
    def _assess_pain_risk(self, responses: Dict[str, Any], days_post_surgery: int) -> Dict[str, Any]:
        """Assess pain-related risk factors"""
        
        pain_level = responses.get("pain_level", 0)
        pain_pattern = responses.get("pain_pattern", "improving")
        pain_medication_effectiveness = responses.get("pain_medication_effectiveness", "effective")
        
        # Determine appropriate thresholds based on days post surgery
        if days_post_surgery <= 7:
            thresholds = self.pain_thresholds["day_1_7"]
        elif days_post_surgery <= 14:
            thresholds = self.pain_thresholds["day_8_14"]
        elif days_post_surgery <= 30:
            thresholds = self.pain_thresholds["day_15_30"]
        else:
            thresholds = self.pain_thresholds["day_30_plus"]
        
        # Assess risk level
        if pain_level >= thresholds["critical"]:
            risk_level = RiskLevel.CRITICAL
        elif pain_level >= thresholds["high"]:
            risk_level = RiskLevel.HIGH
        elif pain_level >= 6 and pain_pattern == "worsening":
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW
        
        return {
            "risk_level": risk_level,
            "pain_level": pain_level,
            "pain_pattern": pain_pattern,
            "medication_effectiveness": pain_medication_effectiveness,
            "flags": self._get_pain_flags(pain_level, pain_pattern, pain_medication_effectiveness)
        }
    
    def _assess_infection_risk(self, responses: Dict[str, Any], days_post_surgery: int) -> Dict[str, Any]:
        """Assess infection risk factors"""
        
        wound_appearance = responses.get("wound_appearance", "normal")
        temperature = responses.get("temperature", 98.6)
        redness = responses.get("wound_redness", False)
        drainage = responses.get("wound_drainage", "none")
        warmth = responses.get("wound_warmth", False)
        
        risk_factors = []
        
        if temperature > 101.0:
            risk_factors.append("fever")
        if wound_appearance in ["red", "inflamed", "concerning"]:
            risk_factors.append("wound_inflammation")
        if drainage in ["purulent", "excessive", "foul_smelling"]:
            risk_factors.append("abnormal_drainage")
        if redness:
            risk_factors.append("wound_redness")
        if warmth:
            risk_factors.append("wound_warmth")
        
        # Determine risk level
        if len(risk_factors) >= 3 or "fever" in risk_factors:
            risk_level = RiskLevel.CRITICAL
        elif len(risk_factors) >= 2:
            risk_level = RiskLevel.HIGH
        elif len(risk_factors) >= 1:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "temperature": temperature,
            "wound_status": wound_appearance
        }
    
    def _assess_mobility_risk(self, responses: Dict[str, Any], days_post_surgery: int) -> Dict[str, Any]:
        """Assess mobility and recovery risk factors"""
        
        mobility_level = responses.get("mobility_level", "normal")
        walking_distance = responses.get("walking_distance", "unlimited")
        stair_climbing = responses.get("stair_climbing", True)
        physical_therapy_compliance = responses.get("pt_compliance", "excellent")
        
        risk_factors = []
        
        # Check mobility against expected milestones
        if days_post_surgery >= 7 and mobility_level in ["bed_bound", "chair_only"]:
            risk_factors.append("delayed_mobility")
        
        if days_post_surgery >= 14 and walking_distance in ["very_limited", "none"]:
            risk_factors.append("limited_walking")
        
        if days_post_surgery >= 14 and not stair_climbing:
            risk_factors.append("stair_difficulty")
        
        if physical_therapy_compliance in ["poor", "inconsistent"]:
            risk_factors.append("pt_noncompliance")
        
        # Determine risk level
        if len(risk_factors) >= 3:
            risk_level = RiskLevel.HIGH
        elif len(risk_factors) >= 2:
            risk_level = RiskLevel.MODERATE
        elif len(risk_factors) >= 1:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.LOW
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "mobility_level": mobility_level,
            "pt_compliance": physical_therapy_compliance
        }
    
    def _assess_medication_risk(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Assess medication-related risk factors"""
        
        medication_compliance = responses.get("medication_compliance", "excellent")
        side_effects = responses.get("medication_side_effects", [])
        pain_medication_overuse = responses.get("pain_med_overuse", False)
        
        risk_factors = []
        
        if medication_compliance in ["poor", "inconsistent"]:
            risk_factors.append("poor_compliance")
        
        if pain_medication_overuse:
            risk_factors.append("medication_overuse")
        
        if "severe" in str(side_effects).lower():
            risk_factors.append("severe_side_effects")
        
        # Determine risk level
        if len(risk_factors) >= 2:
            risk_level = RiskLevel.HIGH
        elif len(risk_factors) >= 1:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "compliance": medication_compliance,
            "side_effects": side_effects
        }
    
    def _assess_psychological_risk(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Assess psychological and emotional risk factors"""
        
        anxiety_level = responses.get("anxiety_level", 0)
        depression_indicators = responses.get("depression_indicators", [])
        sleep_quality = responses.get("sleep_quality", "good")
        social_support = responses.get("social_support", "adequate")
        
        risk_factors = []
        
        if anxiety_level >= 7:
            risk_factors.append("high_anxiety")
        
        if len(depression_indicators) >= 2:
            risk_factors.append("depression_risk")
        
        if sleep_quality in ["poor", "very_poor"]:
            risk_factors.append("sleep_disturbance")
        
        if social_support in ["poor", "none"]:
            risk_factors.append("inadequate_support")
        
        # Determine risk level
        if len(risk_factors) >= 3:
            risk_level = RiskLevel.HIGH
        elif len(risk_factors) >= 2:
            risk_level = RiskLevel.MODERATE
        elif len(risk_factors) >= 1:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.LOW
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "anxiety_level": anxiety_level,
            "sleep_quality": sleep_quality
        }
    
    def _calculate_overall_risk(self, risk_assessments: List[Dict[str, Any]]) -> RiskLevel:
        """Calculate overall risk level from individual assessments"""
        
        risk_scores = {RiskLevel.LOW: 1, RiskLevel.MODERATE: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
        
        total_score = sum(risk_scores[assessment["risk_level"]] for assessment in risk_assessments)
        average_score = total_score / len(risk_assessments)
        
        if average_score >= 3.5:
            return RiskLevel.CRITICAL
        elif average_score >= 2.5:
            return RiskLevel.HIGH
        elif average_score >= 1.5:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    def _generate_clinical_alerts(
        self, 
        patient: Patient, 
        call_session: CallSession, 
        risk_breakdown: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate clinical alerts based on risk assessment"""
        
        alerts = []
        
        for category, risk_data in risk_breakdown.items():
            if risk_data["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                alerts.append({
                    "type": f"{category}_risk",
                    "severity": risk_data["risk_level"].value,
                    "patient_id": patient.id,
                    "call_session_id": call_session.id,
                    "description": f"High {category} risk detected",
                    "risk_factors": risk_data.get("risk_factors", []),
                    "requires_immediate_action": risk_data["risk_level"] == RiskLevel.CRITICAL
                })
        
        return alerts
    
    def _generate_recommendations(
        self, 
        overall_risk: RiskLevel, 
        alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate clinical recommendations based on assessment"""
        
        recommendations = []
        
        if overall_risk == RiskLevel.CRITICAL:
            recommendations.append("Immediate physician contact required")
            recommendations.append("Consider emergency department evaluation")
        elif overall_risk == RiskLevel.HIGH:
            recommendations.append("Schedule urgent follow-up within 24-48 hours")
            recommendations.append("Increase monitoring frequency")
        elif overall_risk == RiskLevel.MODERATE:
            recommendations.append("Schedule follow-up within 1 week")
            recommendations.append("Provide additional patient education")
        
        # Add specific recommendations based on alerts
        for alert in alerts:
            if "pain" in alert["type"]:
                recommendations.append("Review pain management plan")
            elif "infection" in alert["type"]:
                recommendations.append("Evaluate for surgical site infection")
            elif "mobility" in alert["type"]:
                recommendations.append("Physical therapy reassessment")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_days_post_surgery(self, patient: Patient, call_session: CallSession) -> int:
        """Calculate days since surgery"""
        # This would need surgery date from patient record
        # For now, using call session creation as proxy
        if call_session.created_at:
            delta = datetime.utcnow() - call_session.created_at
            return delta.days
        return 0
    
    def _get_pain_flags(self, pain_level: int, pain_pattern: str, medication_effectiveness: str) -> List[str]:
        """Get specific pain-related flags"""
        flags = []
        
        if pain_level >= 8:
            flags.append("severe_pain")
        if pain_pattern == "worsening":
            flags.append("increasing_pain")
        if medication_effectiveness in ["ineffective", "poor"]:
            flags.append("medication_ineffective")
        
        return flags
    
    def assess_conversation_risk(self, responses: Dict[str, Any], call_type: str) -> Dict[str, Any]:
        """
        Streamlined risk assessment for conversation manager integration
        
        Args:
            responses: Dictionary of patient responses by section
            call_type: Type of call (enrollment, education, etc.)
            
        Returns:
            Risk assessment results with escalation recommendations
        """
        risk_indicators = []
        escalation_triggers = []
        
        # Pain assessment
        pain_responses = self._extract_pain_responses(responses)
        if pain_responses:
            pain_risk = self._assess_pain_indicators(pain_responses)
            if pain_risk['escalate']:
                risk_indicators.append(pain_risk)
                escalation_triggers.append(pain_risk['trigger'])
        
        # Support system assessment
        support_responses = self._extract_support_responses(responses)
        if support_responses:
            support_risk = self._assess_support_indicators(support_responses)
            if support_risk['escalate']:
                risk_indicators.append(support_risk)
                escalation_triggers.append(support_risk['trigger'])
        
        # Medical condition assessment
        medical_responses = self._extract_medical_responses(responses)
        if medical_responses:
            medical_risk = self._assess_medical_indicators(medical_responses)
            if medical_risk['escalate']:
                risk_indicators.append(medical_risk)
                escalation_triggers.append(medical_risk['trigger'])
        
        # Calculate overall risk
        overall_risk = self._calculate_conversation_risk_level(risk_indicators)
        
        return {
            'overall_risk': overall_risk,
            'risk_indicators': risk_indicators,
            'escalation_triggers': escalation_triggers,
            'escalation_needed': len(escalation_triggers) > 0,
            'recommendations': self._get_risk_recommendations(overall_risk, escalation_triggers)
        }
    
    def _extract_pain_responses(self, responses: Dict[str, Any]) -> List[str]:
        """Extract pain-related responses from conversation data"""
        pain_responses = []
        pain_sections = ['baseline_mobility_assessment', 'pain_level_evaluation']
        
        for section_name, section_data in responses.items():
            if section_name in pain_sections:
                if isinstance(section_data, list):
                    for item in section_data:
                        if isinstance(item, dict) and 'response' in item:
                            pain_responses.append(item['response'])
                elif isinstance(section_data, str):
                    pain_responses.append(section_data)
        
        return pain_responses
    
    def _extract_support_responses(self, responses: Dict[str, Any]) -> List[str]:
        """Extract support system related responses"""
        support_responses = []
        support_sections = ['support_system_mapping']
        
        for section_name, section_data in responses.items():
            if section_name in support_sections:
                if isinstance(section_data, list):
                    for item in section_data:
                        if isinstance(item, dict) and 'response' in item:
                            support_responses.append(item['response'])
                elif isinstance(section_data, str):
                    support_responses.append(section_data)
        
        return support_responses
    
    def _extract_medical_responses(self, responses: Dict[str, Any]) -> List[str]:
        """Extract medical condition related responses"""
        medical_responses = []
        medical_sections = ['medical_optimization_review']
        
        for section_name, section_data in responses.items():
            if section_name in medical_sections:
                if isinstance(section_data, list):
                    for item in section_data:
                        if isinstance(item, dict) and 'response' in item:
                            medical_responses.append(item['response'])
                elif isinstance(section_data, str):
                    medical_responses.append(section_data)
        
        return medical_responses
    
    def _assess_pain_indicators(self, pain_responses: List[str]) -> Dict[str, Any]:
        """Assess pain-related risk indicators"""
        for response in pain_responses:
            response_lower = response.lower()
            
            # High pain levels
            if any(indicator in response_lower for indicator in ['8', '9', '10', 'severe', 'terrible', 'unbearable', 'excruciating']):
                return {
                    'category': 'pain',
                    'level': 'high',
                    'escalate': True,
                    'trigger': 'severe_pain_reported',
                    'urgency': 'high',
                    'response': response
                }
            
            # Concerning pain descriptions
            if any(indicator in response_lower for indicator in ['getting worse', 'increasing', 'constant', 'never stops']):
                return {
                    'category': 'pain',
                    'level': 'moderate',
                    'escalate': True,
                    'trigger': 'worsening_pain_pattern',
                    'urgency': 'moderate',
                    'response': response
                }
        
        return {'escalate': False}
    
    def _assess_support_indicators(self, support_responses: List[str]) -> Dict[str, Any]:
        """Assess support system risk indicators"""
        for response in support_responses:
            response_lower = response.lower()
            
            # No support system
            if any(indicator in response_lower for indicator in ['no one', 'nobody', 'alone', 'no help', 'by myself']):
                return {
                    'category': 'support',
                    'level': 'high',
                    'escalate': True,
                    'trigger': 'inadequate_support_system',
                    'urgency': 'high',
                    'response': response
                }
            
            # Unreliable support
            if any(indicator in response_lower for indicator in ['sometimes', 'maybe', 'not sure', 'depends']):
                return {
                    'category': 'support',
                    'level': 'moderate',
                    'escalate': True,
                    'trigger': 'unreliable_support_system',
                    'urgency': 'moderate',
                    'response': response
                }
        
        return {'escalate': False}
    
    def _assess_medical_indicators(self, medical_responses: List[str]) -> Dict[str, Any]:
        """Assess medical condition risk indicators"""
        for response in medical_responses:
            response_lower = response.lower()
            
            # Uncontrolled conditions
            if any(indicator in response_lower for indicator in ['uncontrolled', 'high blood pressure', 'not taking', 'forgot medication', 'out of pills']):
                return {
                    'category': 'medical',
                    'level': 'moderate',
                    'escalate': True,
                    'trigger': 'medical_optimization_needed',
                    'urgency': 'moderate',
                    'response': response
                }
            
            # Serious conditions
            if any(indicator in response_lower for indicator in ['heart attack', 'stroke', 'chest pain', 'shortness of breath']):
                return {
                    'category': 'medical',
                    'level': 'high',
                    'escalate': True,
                    'trigger': 'serious_medical_condition',
                    'urgency': 'high',
                    'response': response
                }
        
        return {'escalate': False}
    
    def _calculate_conversation_risk_level(self, risk_indicators: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level from conversation indicators"""
        if not risk_indicators:
            return 'low'
        
        risk_levels = [indicator.get('level', 'low') for indicator in risk_indicators]
        
        if 'high' in risk_levels:
            return 'high'
        elif 'moderate' in risk_levels:
            return 'moderate'
        else:
            return 'low'
    
    def _get_risk_recommendations(self, risk_level: str, escalation_triggers: List[str]) -> List[str]:
        """Get recommendations based on risk assessment"""
        recommendations = []
        
        if 'severe_pain_reported' in escalation_triggers:
            recommendations.append("Contact physician immediately for pain evaluation")
            recommendations.append("Consider pain management consultation")
        
        if 'inadequate_support_system' in escalation_triggers:
            recommendations.append("Arrange additional post-operative support")
            recommendations.append("Consider home health services")
        
        if 'medical_optimization_needed' in escalation_triggers:
            recommendations.append("Medical clearance required before surgery")
            recommendations.append("Optimize chronic conditions")
        
        if risk_level == 'high':
            recommendations.append("Priority follow-up within 24 hours")
        elif risk_level == 'moderate':
            recommendations.append("Follow-up within 48-72 hours")
        
        return recommendations

# Factory function for dependency injection
_clinical_rules_service = None

def get_clinical_rules_service() -> ClinicalRulesService:
    """Get or create ClinicalRulesService instance (singleton pattern)"""
    global _clinical_rules_service
    if _clinical_rules_service is None:
        _clinical_rules_service = ClinicalRulesService()
    return _clinical_rules_service