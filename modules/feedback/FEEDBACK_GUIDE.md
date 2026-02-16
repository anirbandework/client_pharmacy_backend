# 🎯 Engaging Feedback System

An interactive and fun feedback system for admins and staff to share their thoughts, report issues, and suggest improvements.

## ✨ Features

### 🎭 Mood-Based Feedback
Users select their mood while giving feedback:
- 😄 **Excited** - Love the new features!
- 😊 **Happy** - Things are going well
- 😐 **Neutral** - Just sharing thoughts
- 😤 **Frustrated** - Facing some challenges
- 😡 **Angry** - Serious issues need attention

### 📝 Feedback Types
- 🚀 **Feature Request** - "I wish we had..."
- 🐛 **Bug Report** - "Something's not working"
- 💡 **Improvement** - "This could be better"
- 😞 **Complaint** - "I'm not happy with..."
- 💖 **Appreciation** - "Thank you for..."
- 📌 **Other** - "Something else..."

### ⭐ Engagement Features
- **Satisfaction Rating**: 1-5 stars
- **Would Recommend**: Yes/No toggle
- **Priority Auto-Detection**: Based on mood and type
- **Real-time Status Tracking**: pending → reviewed → in_progress → resolved

## 🔌 API Endpoints

### Staff Endpoints

#### Submit Feedback
```http
POST /api/feedback/staff/feedback
Authorization: Bearer {staff_token}

{
  "feedback_type": "feature_request",
  "mood": "excited",
  "title": "Add dark mode please!",
  "message": "Would love to have a dark mode option for night shifts. My eyes get tired looking at the bright screen all night.",
  "would_recommend": true,
  "satisfaction_rating": 4
}
```

#### Get My Feedback History
```http
GET /api/feedback/my-feedback
Authorization: Bearer {staff_token}
```

### Admin Endpoints

#### Submit Feedback
```http
POST /api/feedback/admin/feedback
Authorization: Bearer {admin_token}

{
  "feedback_type": "bug_report",
  "mood": "frustrated",
  "title": "Stock report export not working",
  "message": "When I try to export the stock report, it shows an error. This is urgent as I need it for the monthly meeting.",
  "would_recommend": true,
  "satisfaction_rating": 3
}
```

#### Get My Feedback History
```http
GET /api/feedback/my-feedback
Authorization: Bearer {admin_token}
```

### SuperAdmin Endpoints

#### View All Feedback
```http
GET /api/feedback/super-admin/all-feedback?status=pending&feedback_type=bug_report
Authorization: Bearer {superadmin_token}

Query Parameters:
- status: pending, reviewed, in_progress, resolved, closed
- feedback_type: feature_request, bug_report, improvement, complaint, appreciation, other
- user_type: admin, staff
- organization_id: filter by organization
- skip: pagination offset
- limit: results per page
```

#### Respond to Feedback
```http
PUT /api/feedback/super-admin/feedback/{feedback_id}
Authorization: Bearer {superadmin_token}

{
  "status": "in_progress",
  "priority": "high",
  "admin_response": "Thanks for reporting this! We're working on the dark mode feature and it will be released in the next update."
}
```

#### Get Feedback Statistics
```http
GET /api/feedback/super-admin/feedback-stats
Authorization: Bearer {superadmin_token}

Response:
{
  "total_feedback": 156,
  "pending": 23,
  "resolved": 98,
  "by_type": {
    "feature_request": 45,
    "bug_report": 32,
    "improvement": 28,
    "complaint": 15,
    "appreciation": 30,
    "other": 6
  },
  "by_mood": {
    "excited": 35,
    "happy": 52,
    "neutral": 40,
    "frustrated": 20,
    "angry": 9
  },
  "average_satisfaction": 4.2,
  "recommendation_rate": 87.5
}
```

## 📊 Feedback Response Structure

```json
{
  "id": 1,
  "user_type": "staff",
  "user_id": 5,
  "user_name": "John Doe",
  "user_phone": "+919876543210",
  "user_email": "john@pharmacy.com",
  "shop_id": 1,
  "shop_name": "Main Pharmacy",
  "shop_location": "123 Main Street, Mumbai",
  "organization_id": "ORG001",
  "admin_name": "Admin Kumar",
  "admin_phone": "+919123456789",
  "feedback_type": "feature_request",
  "mood": "excited",
  "title": "Add dark mode please!",
  "message": "Would love to have a dark mode option...",
  "would_recommend": true,
  "satisfaction_rating": 4,
  "priority": "medium",
  "status": "in_progress",
  "admin_response": "Thanks for the suggestion! Working on it.",
  "responded_by": "Super Admin",
  "responded_at": "2026-02-16T20:30:00",
  "created_at": "2026-02-16T18:00:00",
  "updated_at": "2026-02-16T20:30:00"
}
```

## 🎨 Frontend Integration Ideas

### Engaging UI Components

#### 1. Mood Selector (Interactive Emojis)
```jsx
const moods = [
  { value: 'excited', emoji: '😄', label: 'Excited', color: '#10B981' },
  { value: 'happy', emoji: '😊', label: 'Happy', color: '#3B82F6' },
  { value: 'neutral', emoji: '😐', label: 'Neutral', color: '#6B7280' },
  { value: 'frustrated', emoji: '😤', label: 'Frustrated', color: '#F59E0B' },
  { value: 'angry', emoji: '😡', label: 'Angry', color: '#EF4444' }
];
```

#### 2. Feedback Type Cards (Visual Selection)
```jsx
const feedbackTypes = [
  { value: 'feature_request', icon: '🚀', title: 'Feature Request', desc: 'Suggest new features' },
  { value: 'bug_report', icon: '🐛', title: 'Bug Report', desc: 'Report issues' },
  { value: 'improvement', icon: '💡', title: 'Improvement', desc: 'Make it better' },
  { value: 'complaint', icon: '😞', title: 'Complaint', desc: 'Share concerns' },
  { value: 'appreciation', icon: '💖', title: 'Appreciation', desc: 'Say thanks' },
  { value: 'other', icon: '📌', title: 'Other', desc: 'Something else' }
];
```

#### 3. Star Rating Component
```jsx
<StarRating 
  value={rating} 
  onChange={setRating}
  size="large"
  animated
/>
```

#### 4. Would Recommend Toggle
```jsx
<ToggleSwitch
  label="Would you recommend this system?"
  checked={wouldRecommend}
  onChange={setWouldRecommend}
  trueLabel="Yes! 👍"
  falseLabel="Not yet 👎"
/>
```

### Sample Frontend Form

```jsx
const FeedbackForm = () => {
  const [mood, setMood] = useState('');
  const [type, setType] = useState('');
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [rating, setRating] = useState(5);
  const [recommend, setRecommend] = useState(true);

  const handleSubmit = async () => {
    const response = await fetch('/api/feedback/staff/feedback', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        feedback_type: type,
        mood: mood,
        title: title,
        message: message,
        satisfaction_rating: rating,
        would_recommend: recommend
      })
    });
    
    if (response.ok) {
      showSuccessMessage('Thanks for your feedback! 🎉');
    }
  };

  return (
    <div className="feedback-form">
      <h2>Share Your Thoughts 💭</h2>
      
      {/* Mood Selector */}
      <MoodSelector value={mood} onChange={setMood} />
      
      {/* Type Selector */}
      <TypeCards value={type} onChange={setType} />
      
      {/* Title */}
      <Input 
        placeholder="Give it a catchy title..."
        value={title}
        onChange={setTitle}
      />
      
      {/* Message */}
      <Textarea
        placeholder="Tell us more... we're all ears! 👂"
        value={message}
        onChange={setMessage}
        rows={5}
      />
      
      {/* Rating */}
      <StarRating value={rating} onChange={setRating} />
      
      {/* Recommend */}
      <ToggleSwitch
        label="Would you recommend?"
        checked={recommend}
        onChange={setRecommend}
      />
      
      <Button onClick={handleSubmit}>
        Send Feedback 🚀
      </Button>
    </div>
  );
};
```

## 🎯 Priority Auto-Assignment Logic

The system automatically assigns priority based on mood and type:

- **Urgent**: angry mood + (bug_report OR complaint)
- **High**: frustrated mood + bug_report
- **Medium**: neutral mood OR improvement/feature_request
- **Low**: happy/excited mood + appreciation

## 📱 Notification Integration

When SuperAdmin responds to feedback:
1. User receives in-app notification
2. Email notification (if configured)
3. Status badge updates in sidebar

## 🎨 Sidebar Widget Design

### Staff/Admin Sidebar
```
┌─────────────────────────┐
│  💭 Quick Feedback      │
├─────────────────────────┤
│  How are you feeling?   │
│  😄 😊 😐 😤 😡        │
│                         │
│  [Share Your Thoughts]  │
│                         │
│  📊 My Feedback (3)     │
│  ✅ 2 Resolved          │
│  ⏳ 1 In Progress       │
└─────────────────────────┘
```

## 🔔 Success Messages

Make feedback submission rewarding:
- "Thanks for sharing! Your voice matters! 🎉"
- "Feedback received! We're on it! 💪"
- "Your input helps us improve! ⭐"
- "Awesome! We'll get back to you soon! 🚀"

## 📈 Analytics Dashboard (SuperAdmin)

Display:
- Feedback trends over time
- Most common issues
- Satisfaction score trends
- Response time metrics
- Top contributors
- Mood distribution chart

## 🎁 Gamification Ideas (Future)

- **Feedback Champion**: Most helpful feedback
- **Bug Hunter**: Most bugs reported
- **Feature Visionary**: Best feature suggestions
- **Appreciation Star**: Most appreciations given
