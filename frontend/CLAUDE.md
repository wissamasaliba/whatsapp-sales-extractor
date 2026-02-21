
# Frontend Requirements

Build a React frontend for the WhatsApp Sales Extractor Demo app.

## Components

### Navbar
- Company logo on the top left from src/assets/logo.jpg
- App name "WhatsApp Sales Extractor" next to the logo
- Clean minimal design with dark background
- Full width spanning the entire page

### UploadPanel
- Drag and drop area to upload WhatsApp txt file
- Browse button as alternative to drag and drop
- Show file name after selection
- Show loading spinner while Groq is processing

### SalesTable
- Display extracted sales in a clean table
- Columns: Timestamp, Sender, Product, Quantity, Unit Price, Total Price, Currency
- Show errors section below the table for incomplete records
- Empty state message when no sales are loaded yet

### ExportButton
- Button to trigger the export to Excel
- Calls the POST /export endpoint
- Downloads the Excel file automatically
- Disable button when no sales data is loaded

## API Connection
- All components connect to FastAPI backend at http://127.0.0.1:8000
- Use axios for all API calls
- Handle loading states and error messages gracefully

## Design
- Clean modern UI
- Dark navbar with light content area
- Responsive layout
```

Save the file with `Ctrl+S`, then go to Claude Code and type:
```
Read frontend/CLAUDE.md and build the frontend based on those requirements