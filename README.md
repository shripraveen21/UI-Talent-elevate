# Learning Platform

A modern web application built with Angular and Tailwind CSS that provides interactive learning experiences including MCQ quizzes and debugging exercises.

## Features

- **MCQ Quiz**: Interactive multiple-choice questions tailored to your skill level and technology interests
- **Debug Exercise**: Practical exercises to improve debugging skills
- **Agent Chat**: AI-powered learning assistance
- **Modern UI**: Responsive design with Tailwind CSS

## Prerequisites

- Node.js (v14.x or higher)
- npm (v6.x or higher)
- Angular CLI (v19.x)

## Project Setup

### Clone the Repository

```bash
git clone <repository-url>
cd Agents
```

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
ng serve
```

4. Open your browser and navigate to `http://localhost:4200`

### Backend Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the backend server:

```bash
uvicorn app.main:app --port 8002 
```

## Tailwind CSS Configuration

This project uses Tailwind CSS for styling. If you're setting up the project from scratch or need to reconfigure Tailwind, follow these steps:

### 1. Install Required Packages

```bash
npm install -D tailwindcss postcss autoprefixer
```

### 2. Initialize Tailwind CSS

```bash
npx tailwindcss init
```

### 3. Configure PostCSS

Create a `postcss.config.js` file in the root of your frontend directory with the following content:

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

### 4. Configure Tailwind CSS

Update the `tailwind.config.js` file to include your source files and customize the theme:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        // Add other color schemes as needed
      },
    },
  },
  plugins: [],
};
```

### 5. Import Tailwind in Your CSS

Add the following imports to your `src/styles.css` file:

```css
/* Tailwind CSS imports */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Your custom styles below */
```

### 6. Angular Configuration

Ensure your `angular.json` file includes the PostCSS configuration:

```json
{
  "projects": {
    "your-project-name": {
      "architect": {
        "build": {
          "options": {
            "styles": ["src/styles.css"]
          }
        }
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Tailwind classes not working**:
   - Make sure you've imported Tailwind correctly in your styles.css
   - Check that your content paths in tailwind.config.js are correct
   - Clear your browser cache and restart the Angular server

2. **PostCSS errors**:
   - Ensure you're using compatible versions of PostCSS and Tailwind
   - Check that your postcss.config.js is in the correct location

## Project Structure

```
/Agents
  /frontend            # Angular frontend
    /src
      /app
        /components    # Angular components
        /services      # Angular services
      /styles.css      # Global styles with Tailwind imports
    /tailwind.config.js # Tailwind configuration
    /postcss.config.js # PostCSS configuration
  /backend             # Python backend
```

## License

[Your License Here]