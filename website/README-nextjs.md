# AI Image Generator - Next.js

This is a Next.js conversion of the AI image generator website.

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

- `pages/` - Next.js pages (routes)
  - `index.tsx` - Image gallery page
  - `request.tsx` - Image generation request form
  - `_app.tsx` - Global app component
- `components/` - React components
  - `CommonHead.tsx` - Shared head content (meta tags, icons, etc.)
  - `Layout.tsx` - Common layout wrapper
- `styles/` - CSS files
  - `globals.css` - Global styles (imports the original index.css)

## Key Features

- **Shared Head Content**: The `CommonHead` component provides a centralized way to manage meta tags, favicons, and other head elements
- **Layout Component**: Wraps pages with common structure and head content
- **TypeScript**: Full TypeScript support for better development experience
- **API Proxying**: Next.js config proxies `/api/*` requests to the external API
- **Responsive Design**: Maintains all mobile-friendly features from the original

## Migration Benefits

- **Component Reusability**: Head content and layout can be easily shared across pages
- **Better Performance**: Next.js optimization and code splitting
- **Developer Experience**: Hot reloading, TypeScript support, better error handling
- **SEO**: Better server-side rendering capabilities
- **Maintainability**: Organized component structure and TypeScript

## Usage

The `CommonHead` component accepts optional props:
- `title` - Page title (defaults to "AI Image Generator")
- `description` - Meta description (defaults to generic description)

Example:
```tsx
<CommonHead 
  title="Custom Page Title" 
  description="Custom page description" 
/>
```
