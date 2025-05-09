# Habit AI - Intelligent Goal and Task Management System

An AI-powered habit and goal tracking application that helps users break down their goals into manageable daily tasks, using smart task generation and progress analysis to provide personalized suggestions.

## Features

### Goal Management
- Set up detailed goals with descriptions and target dates
- Track motivation factors and consequences of inaction
- View active goals on a central dashboard

### Intelligent Task Generation
- AI-powered task suggestions based on:
  - Goal context and description
  - Recent task history analysis
  - Success rate adaptation
  - User's optimal performance time patterns
  - Progress tracking and momentum building

### Task Management
- Generate daily tasks with AI assistance
- Add custom tasks manually
- Mark tasks as Complete, Missed, or Reset status
- View task history and progress

### Smart Adaptation
The system adapts task suggestions based on your performance:
- Success rate < 30%: Generates easier, more achievable tasks
- Success rate 30-70%: Maintains moderate difficulty
- Success rate > 70%: Increases challenge level appropriately

### Time Optimization
- Analyzes user's peak performance times (morning/afternoon/evening)
- Incorporates preferred time periods into task suggestions
- Provides context-aware task timing recommendations

## Technical Architecture

### Backend (Python/Flask)
- Flask web application server
- SQLite database for data persistence
- Google's Gemini AI model integration for task generation
- RESTful API endpoints for goal and task management

### Database Schema
- Users table: Stores user information and preferences
- Goals table: Stores goal details, motivations, and target dates
- Tasks table: Manages task descriptions, due dates, and completion status

### Frontend
- HTML templates with Jinja2 templating
- Clean, responsive design
- Interactive task management interface
- Real-time task generation and updates

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with:
```
GOOGLE_API_KEY=your_gemini_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5001`

## Task Generation Logic

The task generation system uses a sophisticated algorithm that considers multiple factors:

1. **Goal Context**
   - Main goal description
   - Target completion date
   - User's motivation factors
   - Potential consequences of inaction

2. **Progress Analysis**
   - Reviews last 10 tasks
   - Calculates success rate
   - Identifies completion patterns
   - Avoids repeating recent tasks

3. **Performance Optimization**
   - Tracks optimal completion times
   - Analyzes success patterns
   - Adapts difficulty based on performance
   - Builds on previous successes

4. **Task Generation Rules**
   - Tasks must be specific and actionable
   - Difficulty adjusts based on success rate
   - Incorporates user's preferred timing
   - Ensures direct relation to main goal
   - Must be completable within one day

## API Endpoints

- `/`: Main dashboard
- `/setup_goal`: Goal creation interface
- `/goal/<goal_id>`: Goal details and tasks
- `/generate_task_for_today`: Generate AI task suggestions
- `/save_task`: Save generated or custom tasks
- `/task/<task_id>/complete`: Mark task as complete
- `/task/<task_id>/missed`: Mark task as missed
- `/task/<task_id>/reset`: Reset task status

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
