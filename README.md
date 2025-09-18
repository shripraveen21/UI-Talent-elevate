# TalentElevate - Debug-gen and Hands-on-gen Components Documentation

This document provides a comprehensive overview of the UI flows, fields, and interactions for the `debug-gen` and `hands-on-gen` components in the TalentElevate project. This documentation is designed to serve as input for Lovable AI to redesign these components into modern, styled UI pages.

## Debug-gen Component

The Debug-gen component is responsible for generating debugging exercises with human-in-the-loop review capabilities.

### Initial Stage

**Page Header:**
- Title: "Debug Exercise Generator"
- Subtitle: "Create debugging challenges for technical assessments"

**Exercise Configuration Card:**

When accessed via query parameters (read-only mode):
- **Tech Stack** (read-only span): Displays the technology stack passed from navigation
- **Concepts** (read-only span): Displays the concepts passed from navigation

When accessed directly (input mode):
- **Tech Stack** (dropdown select):
  - Label: "Tech Stack"
  - Placeholder: "Select Tech Stack"
  - Options: Angular, React, Node.js, Python, Java, .NET, PHP, Ruby
- **Concepts** (textarea):
  - Label: "Concepts"
  - Placeholder: "Enter concepts (comma-separated)"
  - Rows: 3

**Form Fields:**
- **Difficulty Level** (dropdown select):
  - Label: "Difficulty Level"
  - Options: Beginner, Intermediate, Advanced
- **Duration** (number input):
  - Label: "Duration (minutes)"
  - Placeholder: "Enter duration"
  - Min: 1, Max: 180

**Actions:**
- **"Generate Debug Exercise"** button (primary blue button)

### After Input

**Status Display:**
- Status indicator showing "Generating..." with loading animation
- WebSocket connection status messages

**Generated Content Display:**
- **BRD (Business Requirements Document)** section:
  - Content displayed in a formatted text area with monospace font
  - Background: Light gray (#f9fafb)
  - Border: Rounded corners with subtle border

### Human-in-the-Loop

**BRD Review Section:**
- **"Review and Edit BRD"** header
- **Editable BRD Content** (large textarea):
  - Pre-populated with generated BRD content
  - Full editing capabilities
  - Monospace font for code formatting

**Actions:**
- **"Approve BRD"** button (success green button)
- **"Regenerate BRD"** button (secondary gray button)

**Project Information Display:**
- **Project Structure** section:
  - Displays generated project files and structure
  - Read-only formatted display
- **Bug Information** section:
  - Shows details about the introduced bugs
  - Read-only formatted display

### Save/Submit

**Final Actions:**
- **"Save Debug Exercise"** button (primary blue button)
- **"Back to Dashboard"** button (secondary gray button)

**Success State:**
- Success message: "Debug exercise saved successfully!"
- Green status indicator

**Error State:**
- Error message display in red
- Error details if available

---

## Hands-on-gen Component

The Hands-on-gen component is responsible for generating hands-on coding projects with SRS (Software Requirements Specification) review capabilities.

### Initial Stage

**Page Header:**
- Title: "Hands-On Project Generator"
- Subtitle: "Create practical coding projects for technical assessments"

**Project Setup Card:**

When accessed via query parameters (read-only mode):
- **Tech Stack** (read-only span): Displays the technology stack passed from navigation
- **Concepts** (read-only span): Displays the concepts passed from navigation

When accessed directly (input mode):
- **Tech Stack** (dropdown select):
  - Label: "Tech Stack"
  - Placeholder: "Select Tech Stack"
  - Options: Angular, React, Node.js, Python, Java, .NET, PHP, Ruby
- **Concepts** (textarea):
  - Label: "Concepts"
  - Placeholder: "Enter concepts (comma-separated)"
  - Rows: 3

**Form Fields:**
- **Duration** (number input):
  - Label: "Duration (hours)"
  - Placeholder: "Enter duration"
  - Min: 1, Max: 8

**Actions:**
- **"Generate Hands-On Project"** button (primary blue button)

### After Input

**Status Display:**
- Status indicator showing "Generating..." with loading animation
- WebSocket connection status messages

**Generated Content Display:**
- **SRS (Software Requirements Specification)** section:
  - Content displayed in a formatted text area with monospace font
  - Background: Light gray (#f9fafb)
  - Border: Rounded corners with subtle border

### Human-in-the-Loop

**SRS Review Section:**
- **"Review and Edit SRS"** header
- **Editable SRS Content** (large textarea):
  - Pre-populated with generated SRS content
  - Full editing capabilities
  - Monospace font for technical documentation

**Actions:**
- **"Approve SRS"** button (success green button)
- **"Regenerate SRS"** button (secondary gray button)

**Final SRS Approved Section:**
- **Final SRS Display** (read-only):
  - Shows the approved SRS content
  - Formatted display with proper styling
  - Background: Light background for readability

### Save/Submit

**Project Saved Confirmation:**
- **"Project Saved Successfully!"** message
- Green success indicator
- Confirmation details

**Final Actions:**
- **"Save Hands-On Project"** button (primary blue button)
- **"Back to Dashboard"** button (secondary gray button)

**Error State:**
- Error message display in red
- Error details if available

---

## Common UI Elements and Styling

### Visual Design System

**Color Palette:**
- Primary Blue: `hsl(217, 91%, 60%)` - Used for primary buttons and focus states
- Success Green: `#10b981` - Used for success buttons and positive status
- Warning Yellow: `#fbbf24` - Used for warning states
- Error Red: `#ef4444` - Used for error states and messages
- Gray Scale: Various shades from `#f9fafb` to `#374151` for backgrounds and text

**Typography:**
- Headers: Bold, larger font sizes with proper hierarchy
- Labels: Semi-bold, smaller font size (`0.875rem`)
- Content: Monospace font (`JetBrains Mono`) for code/technical content
- Regular text: Standard sans-serif font

**Interactive Elements:**
- **Buttons**: Rounded corners (12px), gradient backgrounds, hover effects with transform and shadow
- **Input Fields**: Rounded corners (12px), focus states with blue border and shadow
- **Cards**: Elevated appearance with shadows, hover effects with slight transform
- **Status Indicators**: Pill-shaped with appropriate color coding

**Animations:**
- Fade-in animations for page load
- Slide-in animations for status updates
- Pulse animations for loading states
- Hover transforms for interactive elements

### Responsive Design

**Mobile Adaptations:**
- Full-width buttons on mobile devices
- Adjusted padding and margins for smaller screens
- Stacked layouts for form elements
- Reduced font sizes for better mobile readability

**Accessibility Features:**
- Focus states for all interactive elements
- High contrast mode support
- Reduced motion support for users with motion sensitivity
- Proper ARIA labels and semantic HTML structure

### WebSocket Integration

Both components utilize WebSocket connections for real-time updates during the generation process:
- Connection status indicators
- Real-time progress updates
- Error handling for connection issues
- Automatic reconnection capabilities

---

## Technical Implementation Notes

### Navigation Flow
- Components can be accessed directly or via navigation from `create-assessment` component
- Query parameters (`tech_stack` and `concepts`) are used to pre-populate fields when navigating from assessment creation
- Session storage fallback for data persistence

### Data Flow
- Form validation before submission
- WebSocket communication for generation processes
- Human-in-the-loop review stages with edit capabilities
- Final save operations with success/error handling

### State Management
- Component-level state management for form data
- WebSocket state tracking
- Loading and error state management
- Session persistence for user data

This documentation provides the complete UI specification for both components, including all fields, interactions, and visual states as they currently exist in the codebase.