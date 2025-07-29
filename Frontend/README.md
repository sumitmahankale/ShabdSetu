# ShabdSetu Frontend

A modern React-based frontend for the ShabdSetu English to Marathi translation service.

## Features

- 🎨 Modern, responsive UI with Tailwind CSS
- 🚀 Fast development with Vite
- 🌐 Real-time translation interface
- 🔊 Text-to-speech for both languages
- 📋 Copy to clipboard functionality
- 📱 Mobile-friendly design
- 🎯 Quick sample texts for testing
- ♿ Accessible design

## Tech Stack

- **React 18** - Modern UI library
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **Lucide React** - Beautiful icons

## Getting Started

### Prerequisites

- Node.js 16+ and npm

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Visit `http://localhost:3000`

### Backend Connection

Make sure your FastAPI backend is running on `http://localhost:8000`. The frontend is configured to proxy API requests automatically.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Features Overview

### Translation Interface
- **Input Panel**: Type or paste English text
- **Output Panel**: View Marathi translations
- **Real-time**: Instant translations as you type
- **Copy Function**: One-click copy to clipboard

### Audio Features
- **Text-to-Speech**: Click speaker icons to hear pronunciation
- **Multi-language**: Supports both English and Hindi/Marathi voices

### User Experience
- **Quick Samples**: Pre-loaded example texts
- **Keyboard Shortcuts**: Ctrl+Enter to translate
- **Mobile Responsive**: Works on all devices
- **Error Handling**: Clear error messages and retry options

### Accessibility
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: ARIA labels and semantic HTML
- **High Contrast**: Clear visual hierarchy
- **Focus Management**: Proper focus indicators

## Customization

### Styling
The app uses Tailwind CSS for styling. Key style files:
- `src/index.css` - Global styles and custom components
- `tailwind.config.js` - Tailwind configuration

### API Configuration
Backend URL can be changed in:
- `vite.config.js` - Proxy configuration
- `src/App.jsx` - API_BASE_URL constant

## Project Structure

```
Frontend/
├── public/
│   ├── logo.svg           # App logo
│   └── index.html         # HTML template
├── src/
│   ├── App.jsx           # Main application component
│   ├── main.jsx          # React entry point
│   └── index.css         # Global styles
├── package.json          # Dependencies and scripts
├── vite.config.js        # Vite configuration
├── tailwind.config.js    # Tailwind configuration
└── postcss.config.js     # PostCSS configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Browser Support

- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

## License

MIT License - see the LICENSE file for details.
