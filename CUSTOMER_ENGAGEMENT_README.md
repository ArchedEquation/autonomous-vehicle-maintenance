# Customer Engagement Agent - Voice/Chat Capable

## Overview

The Customer Engagement Agent is an AI-powered conversational system that handles customer communication for vehicle maintenance scheduling. It features sentiment analysis, response prediction, natural dialogue generation, objection handling, and intelligent escalation to human agents.

## Key Features

### 1. Multi-Channel Communication
- **Phone Call**: Voice-capable for urgent/critical issues
- **SMS**: Quick text-based communication
- **Email**: Detailed information delivery
- **App Notification**: Push notifications
- **Chat**: Real-time messaging

### 2. Sentiment Analysis
- Real-time sentiment tracking (-1 to 1 scale)
- ML-based analysis using fine-tuned BERT model
- Rule-based fallback for reliability
- Sentiment history tracking
- Automatic escalation on negative sentiment

### 3. Response Prediction
- Predicts customer response likelihood:
  - **ACCEPT**: Ready to schedule
  - **DECLINE**: Not interested
  - **RESCHEDULE**: Wants different time
  - **NEED_INFO**: Has questions/objections
  - **FRUSTRATED**: Negative experience
  - **UNCERTAIN**: Needs more information

### 4. Natural Dialogue Generation
- Context-aware message generation
- Personalized based on:
  - Urgency level (CRITICAL/URGENT/PREVENTIVE/ROUTINE)
  - Communication style (formal/casual/technical)
  - Customer profile
  - Conversation history
- Empathetic, non-robotic language
- Time-of-day appropriate greetings

### 5. Objection Handling
- Identifies objection types:
  - **Cost**: Price concerns
  - **Time**: Scheduling conflicts
  - **Trust**: Skepticism about diagnosis
  - **General**: Other concerns
- Tailored responses for each objection type
- Multiple fallback strategies
- Tracks objection count for escalation

### 6. Intelligent Escalation
- Automatic escalation triggers:
  - Low confidence score (< 0.7)
  - Negative sentiment (< -0.5)
  - Multiple objections (≥ 3)
  - Customer frustration detected
- Smooth handoff to human agents
- Context preservation for human agent

### 7. Preference Capture
- Time slot preferences (morning/afternoon/evening)
- Service center location
- Loaner vehicle needs
- Communication preferences
- Stored for future interactions

### 8. Multi-Modal Notifications
- Voice confirmation during call
- SMS backup confirmation
- Email detailed confirmation
- App push notification
- 24-hour reminder system

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Diagnostic Report (from Master Agent)           │
│  • Urgency Level                                             │
│  • Issues Detected                                           │
│  • Recommended Services                                      │
│  • Estimated Cost                                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Customer Engagement Agent                       │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 1. Channel Selection (based on urgency)               │ │
│  │ 2. Greeting Generation (personalized)                 │ │
│  │ 3. Issue Explanation (natural language)               │ │
│  │ 4. Sentiment Analysis (real-time)                     │ │
│  │ 5. Response Prediction (ML-based)                     │ │
│  │ 6. Objection Handling (if needed)                     │ │
│  │ 7. Preference Gathering                               │ │
│  │ 8. Appointment Scheduling                             │ │
│  │ 9. Confirmation & Notifications                       │ │
│  │ 10. Escalation (if needed)                            │ │
│  └───────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Engagement Result                               │
│  • Outcome (accept/decline/reschedule)                      │
│  • Appointment Details                                       │
│  • Customer Preferences                                      │
│  • Sentiment Score                                           │
│  • Conversation Transcript                                   │
│  • Escalation Status                                         │
└─────────────────────────────────────────────────────────────┘
```

## Conversation Flow

### State Machine

```
GREETING
  ↓
ISSUE_EXPLANATION
  ↓
SCHEDULING / OBJECTION_HANDLING
  ↓
PREFERENCE_GATHERING
  ↓
CONFIRMATION
  ↓
COMPLETED / ESCALATION
```

### Example Conversations

#### Critical Issue (Formal Style)

```
AGENT: Good morning, Michael. This is Sarah from AutoCare Services. 
       How are you today?

CUSTOMER: I'm good, thanks. What's this about?

AGENT: I'm calling because our diagnostic system has detected a critical 
       issue with your vehicle. We've identified engine overheating, 
       coolant leak, and thermostat failure issues. For your safety, 
       we strongly recommend immediate service. Can we schedule an 
       appointment for you today?

CUSTOMER: Oh no, that sounds serious! Yes, let's schedule something 
          right away.

AGENT: Great! Let me find the best time for you. Do you prefer morning, 
       afternoon, or evening appointments?

CUSTOMER: Morning works best for me, around 9 AM if possible.

AGENT: Perfect! I've scheduled your appointment for tomorrow at 9:00 AM 
       at our Main Center service center. You'll receive a confirmation 
       via phone call. Is there anything else I can help you with?
```

#### Preventive Maintenance (Casual Style)

```
AGENT: Hi Jennifer! This is Sarah from AutoCare. How's your day going?

CUSTOMER: Hi, I'm a bit busy. What do you need?

AGENT: So, your vehicle is showing brake pad wear and battery degradation. 
       It's not an emergency, but we should probably get it looked at in 
       the next day or two. How's your schedule this week?

CUSTOMER: Hmm, how much is this going to cost?

AGENT: That's a fair question. The estimated cost is $450.00, which 
       includes brake inspection, brake pad replacement, and battery test. 
       We also offer payment plans if that would help. Would you like to 
       hear about those options?

CUSTOMER: Okay, that makes sense. Let's go ahead and schedule it.

AGENT: Excellent! Your appointment is confirmed: next Tuesday at 2:00 PM, 
       Main Center. We'll take good care of your vehicle. See you then!
```

## Usage

### Basic Setup

```python
from customer_engagement_agent import (
    CustomerEngagementAgent,
    DiagnosticReport,
    CustomerProfile,
    UrgencyLevel,
    CommunicationChannel
)

# Initialize agent
agent = CustomerEngagementAgent(
    sentiment_model_path='sentiment_model_weights',
    confidence_threshold=0.7,
    escalation_sentiment_threshold=-0.5
)
```

### Engage Customer

```python
# Create diagnostic report
report = DiagnosticReport(
    vehicle_id='VEH001',
    customer_id='CUST001',
    urgency_level=UrgencyLevel.CRITICAL,
    issues_detected=['engine overheating', 'coolant leak'],
    recommended_services=['cooling_system_repair', 'thermostat_replacement'],
    estimated_cost=850.00,
    risk_description='immediate engine damage risk',
    time_to_failure_days=1,
    safety_critical=True
)

# Create customer profile
customer = CustomerProfile(
    customer_id='CUST001',
    name='John Smith',
    phone='+1-555-0100',
    email='john@example.com',
    preferred_channel=CommunicationChannel.PHONE_CALL,
    preferred_time='morning',
    communication_style='formal'
)

# Engage customer
result = agent.engage_customer(report, customer)

# Check result
print(f"Outcome: {result.outcome.value}")
print(f"Scheduled: {result.appointment_scheduled}")
print(f"Sentiment: {result.sentiment_score}")
```

### Integration with Master Orchestrator

```python
from customer_engagement_agent import create_customer_engagement_handler
from master_orchestrator import MasterOrchestrator, AgentType

# Create orchestrator
orchestrator = MasterOrchestrator()

# Create and register handler
handler = create_customer_engagement_handler(agent)
orchestrator.register_agent(AgentType.CUSTOMER_ENGAGEMENT, handler)

# Start orchestrator
orchestrator.start()
```

## Dialogue Templates

### Urgency-Based Templates

#### Critical Issue
```
"I'm calling because our diagnostic system has detected a critical issue 
with your {vehicle}. {issue_description}. For your safety, we strongly 
recommend immediate service. Can we schedule an appointment for you today?"
```

#### Urgent Issue
```
"Our diagnostic analysis indicates your {vehicle} has {issue_description}. 
While not immediately critical, this issue could lead to a breakdown within 
the next few days. We'd like to schedule service within 48 hours."
```

#### Preventive
```
"Good news - we're being proactive! Our analysis suggests your {vehicle} 
would benefit from preventive maintenance to avoid potential issues. 
Specifically, {issue_description}."
```

#### Routine
```
"Hello {name}, this is a courtesy reminder that your {vehicle} is due for 
scheduled maintenance. It's been {time_since_last} since your last service."
```

### Objection Responses

#### Cost Objection
```
"I understand cost is a concern. Let me break down what we're looking at: 
{cost_breakdown}. Keep in mind, addressing this now will likely save you 
money compared to waiting for a more serious failure."
```

#### Time Objection
```
"I completely understand you're busy. The service will take approximately 
{duration} hours. We also offer loaner vehicles so you don't have to wait. 
Would that work better for you?"
```

#### Trust Objection
```
"I appreciate your caution. Our diagnostic system uses advanced AI and has 
been validated by certified technicians. We're happy to show you the 
diagnostic data and have a technician explain everything."
```

## Sentiment Analysis

### Scoring System

| Score Range | Label | Action |
|-------------|-------|--------|
| 0.5 to 1.0 | Very Positive | Continue normally |
| 0.2 to 0.5 | Positive | Continue normally |
| -0.2 to 0.2 | Neutral | Monitor closely |
| -0.5 to -0.2 | Negative | Use empathy, prepare escalation |
| -1.0 to -0.5 | Very Negative | Escalate to human |

### ML-Based Analysis

Uses fine-tuned BERT model from `sentiment_model_weights/`:
- Tokenizes customer message
- Generates sentiment logits
- Converts to -1 to 1 scale
- Tracks sentiment history

### Rule-Based Fallback

Counts positive and negative keywords:
- **Positive**: yes, sure, okay, great, good, thanks
- **Negative**: no, not, can't, won't, busy, expensive, frustrated

## Response Prediction

### Prediction Logic

```python
# Clear acceptance indicators
if 'yes' or 'sure' or 'schedule' in message:
    return ACCEPT

# Clear decline indicators
if 'no' or 'not interested' in message:
    return DECLINE

# Reschedule indicators
if 'later' or 'another time' in message:
    return RESCHEDULE

# Frustration indicators
if 'annoyed' or 'frustrated' or 'stop calling' in message:
    return FRUSTRATED

# Information need indicators
if 'why' or 'how much' or 'explain' in message:
    return NEED_INFO
```

## Escalation Logic

### Automatic Escalation Triggers

1. **Low Confidence**: confidence_score < 0.7
2. **Negative Sentiment**: sentiment < -0.5
3. **Multiple Objections**: objections_count ≥ 3
4. **Customer Frustration**: predicted_response == FRUSTRATED

### Escalation Process

```python
if should_escalate(context):
    # Inform customer
    message = "I want to make sure you get the best service possible. 
               Let me connect you with one of our senior service advisors."
    
    # Transfer context to human agent
    # - Conversation history
    # - Customer profile
    # - Diagnostic report
    # - Sentiment analysis
    # - Objections raised
```

## Notification System

### Multi-Channel Notifications

After successful scheduling:

1. **Voice Confirmation** (if phone call)
   - Verbal confirmation during call
   - Repeat key details

2. **SMS Backup**
   ```
   AutoCare: Your service appointment is confirmed for [DATE] at [TIME] 
   at [LOCATION]. Reply CANCEL to cancel.
   ```

3. **Email Confirmation**
   - Detailed appointment information
   - Services list
   - Cost breakdown
   - Directions to service center
   - Contact information

4. **App Push Notification**
   ```json
   {
     "type": "appointment_scheduled",
     "title": "Service Appointment Confirmed",
     "body": "Your vehicle service is scheduled for [DATE] at [TIME]",
     "data": { appointment_details }
   }
   ```

5. **24-Hour Reminder**
   - Sent day before appointment
   - All channels
   - Option to reschedule

## Configuration

### Agent Parameters

```python
CustomerEngagementAgent(
    sentiment_model_path='sentiment_model_weights',  # BERT model path
    confidence_threshold=0.7,                        # Min confidence
    escalation_sentiment_threshold=-0.5              # Escalation trigger
)
```

### Customization

#### Add Custom Dialogue Templates

```python
agent.dialogue_templates['custom_scenario'] = {
    'formal': ["Template 1", "Template 2"],
    'casual': ["Template 3", "Template 4"]
}
```

#### Add Custom Objection Handlers

```python
agent.objection_patterns['custom_objection'] = [
    r'pattern1', r'pattern2'
]
```

## Performance Metrics

### Tracked Statistics

- `total_engagements`: Total customer interactions
- `successful_schedules`: Appointments scheduled
- `escalations`: Escalated to human
- `declined`: Customer declined service
- `average_sentiment`: Average sentiment score
- `success_rate`: Schedule rate
- `escalation_rate`: Escalation rate

### Get Statistics

```python
stats = agent.get_statistics()
print(f"Success Rate: {stats['success_rate']*100:.1f}%")
print(f"Escalation Rate: {stats['escalation_rate']*100:.1f}%")
```

## Running Demos

### All Demos
```bash
python customer_engagement_demo.py
```

### Specific Scenarios
```bash
# Critical scenario
python customer_engagement_demo.py critical

# Preventive maintenance
python customer_engagement_demo.py preventive

# Routine maintenance
python customer_engagement_demo.py routine

# Multi-channel test
python customer_engagement_demo.py multichannel

# Sentiment analysis
python customer_engagement_demo.py sentiment
```

### Standalone Agent Test
```bash
python customer_engagement_agent.py
```

## Best Practices

### 1. Personalization
- Use customer name frequently
- Match communication style
- Reference previous interactions
- Adapt to time of day

### 2. Empathy
- Acknowledge concerns
- Show understanding
- Avoid pressure tactics
- Offer alternatives

### 3. Clarity
- Explain issues clearly
- Avoid technical jargon (unless customer prefers)
- Provide specific details
- Confirm understanding

### 4. Efficiency
- Get to the point quickly for urgent issues
- Respect customer's time
- Offer convenient options
- Minimize back-and-forth

### 5. Escalation
- Escalate early if uncertain
- Preserve conversation context
- Smooth handoff to human
- Don't frustrate customer

## Integration Points

### Input
- Diagnostic reports from Master Orchestrator
- Customer profiles from CRM
- Historical interaction data
- Sentiment model predictions

### Output
- Engagement results
- Appointment details
- Customer preferences
- Conversation transcripts
- Sentiment analysis
- Escalation triggers

## Future Enhancements

1. **Voice Recognition**
   - Real-time speech-to-text
   - Voice emotion detection
   - Natural voice synthesis

2. **Advanced NLP**
   - Intent classification
   - Entity extraction
   - Context understanding
   - Multi-turn dialogue

3. **Personalization**
   - Learning from interactions
   - Adaptive communication style
   - Predictive preferences
   - Relationship building

4. **Multi-Language**
   - Language detection
   - Translation
   - Cultural adaptation
   - Localized templates

5. **Analytics**
   - Conversation analytics
   - Success pattern identification
   - A/B testing
   - Performance optimization

## Troubleshooting

### Issue: Low success rate

**Solutions:**
- Review dialogue templates
- Adjust confidence threshold
- Improve objection handling
- Analyze failed conversations

### Issue: High escalation rate

**Solutions:**
- Lower escalation threshold
- Improve sentiment analysis
- Add more objection handlers
- Better initial explanation

### Issue: Sentiment analysis inaccurate

**Solutions:**
- Fine-tune sentiment model
- Expand keyword lists
- Consider context better
- Use conversation history

## License

[Your License Here]

## Support

For issues or questions, contact [Your Contact Info]
