# AI Contract Risk Analyzer - Frontend

A modern React web application for analyzing contract PDFs and detecting risky clauses using AI-powered similarity search.

## Features

- 📄 **PDF Upload**: Drag-and-drop or click to upload contract PDFs
- 🔍 **AI Analysis**: Automatic clause extraction and risk assessment
- 🎨 **Modern UI**: Clean, responsive design with TailwindCSS
- 📊 **Risk Visualization**: Color-coded risk levels (HIGH/MEDIUM/LOW) with detailed explanations
- 📈 **Summary Statistics**: Overview of risk distribution across clauses

## Tech Stack

- **React** 19.2 - UI framework
- **Vite** 8.0 - Build tool and dev server
- **TailwindCSS** 3.x - Utility-first CSS framework
- **FastAPI Backend** - Python-based API for contract analysis

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+ with the backend API running on `http://localhost:8000`

## Installation

Install dependencies:

```bash
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Build for Production

Create an optimized production build:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

## Usage

1. **Start the Backend**: Ensure the FastAPI backend is running on port 8000

   ```bash
   # From the project root directory
   python api.py
   ```

2. **Start the Frontend**: Run the Vite dev server

   ```bash
   npm run dev
   ```

3. **Upload a Contract**:
   - Drag and drop a PDF file into the upload zone, or click to browse
   - Only PDF files are accepted (max 10MB)

4. **Analyze**: Click the "Analyze Contract" button

5. **View Results**:
   - See the risk summary showing HIGH/MEDIUM/LOW clause counts
   - Scroll through individual clause cards with detailed risk analysis
   - Each card shows the clause text, risk level, and explanation

## API Integration

The frontend communicates with the FastAPI backend via:

**Endpoint**: `POST http://localhost:8000/analyze`

**Request**: Multipart form data with field `file` (PDF)

**Response**:

```json
{
  "results": [
    {
      "clause": "Contract clause text...",
      "risk_level": "HIGH" | "MEDIUM" | "LOW",
      "explanation": "Detailed risk explanation..."
    }
  ]
}
```

## Component Structure

```
src/
├── App.jsx                      # Main app component with state management
├── main.jsx                     # React entry point
├── index.css                    # TailwindCSS imports
└── components/
    ├── Header.jsx               # App title and subtitle
    ├── FileUpload.jsx           # Drag-and-drop PDF upload
    ├── LoadingIndicator.jsx     # Analysis loading state
    ├── ResultsList.jsx          # Results container with summary
    └── ClauseCard.jsx           # Individual clause risk card
```

## Error Handling

The app handles common errors gracefully:

- **Invalid file type**: Displays error if non-PDF file is uploaded
- **File too large**: Warns if file exceeds 10MB
- **Backend unavailable**: Shows user-friendly message with retry option
- **Analysis failures**: Displays detailed error information

## Styling

Uses TailwindCSS utility classes for:

- Responsive layouts (mobile-first approach)
- Color-coded risk levels
- Smooth transitions and hover effects
- Modern gradient backgrounds
- Shadow and border styling

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

Part of the Legal Contract Risk Analyzer system.
