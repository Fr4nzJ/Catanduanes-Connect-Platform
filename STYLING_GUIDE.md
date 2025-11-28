# 🎨 Styling Guide - Color & Component Reference

## Color Palette

### Primary Gradients
```
Blue Gradient:
  - from-blue-50 to-indigo-100 (background)
  - from-blue-600 to-indigo-600 (primary actions)
  - blue-600 (text highlights)

Green Gradient:
  - from-green-50 to-green-100 (success backgrounds)
  - from-green-600 to-emerald-600 (green actions)
  - green-600 (positive indicators)

Purple Gradient:
  - from-purple-50 to-purple-100 (alternative backgrounds)
  - from-purple-600 to-indigo-600 (purple actions)
  - purple-600 (secondary highlights)

Yellow Accents:
  - yellow-300 (featured badges, highlights)
  - yellow-400 (important indicators)

Red Accents:
  - red-500 to red-600 (destructive actions, alerts)
```

---

## Component Library

### Headers
**Usage**: Page titles and section headers

```html
<!-- Blue Header -->
<div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
    <div class="flex items-center gap-3 mb-2">
      <i class="fas fa-icon text-3xl text-yellow-300"></i>
      <h1 class="text-4xl font-bold text-white">Page Title</h1>
    </div>
    <p class="text-blue-100">Subtitle or description</p>
  </div>
</div>
```

**Classes**:
- `bg-gradient-to-r from-[primary]-600 to-[secondary]-600`
- `text-white` for text
- `text-blue-100` for subtitles
- `py-10` for vertical padding
- `px-4 sm:px-6 lg:px-8` for responsive padding

---

### Cards
**Usage**: Content containers, listings, statistics

```html
<!-- Interactive Card -->
<div class="bg-white rounded-xl shadow-lg hover:shadow-2xl 
            hover:scale-105 transition-all duration-300 p-8">
  <!-- Card Header (Optional) -->
  <div class="bg-gradient-to-r from-blue-500 to-indigo-600 
              p-6 -mx-8 -mt-8 mb-6 text-white rounded-t-xl">
    <h3 class="text-2xl font-bold">Card Title</h3>
  </div>
  
  <!-- Card Content -->
  <div class="space-y-4">
    <p class="text-gray-700">Card content goes here</p>
  </div>
</div>
```

**Classes**:
- `bg-white` base
- `rounded-xl` corners (16px)
- `shadow-lg` default shadow
- `hover:shadow-2xl` on hover
- `hover:scale-105` scale animation
- `transition-all duration-300` smooth transition
- `p-8` padding (adjust as needed)

---

### Buttons
**Usage**: Call-to-action, form submission, navigation

```html
<!-- Primary Button -->
<a href="#" class="inline-flex items-center gap-2 
                   bg-gradient-to-r from-blue-600 to-indigo-600 
                   text-white px-8 py-4 rounded-lg 
                   font-semibold hover:shadow-lg hover:scale-105 
                   transition-all duration-300">
  <i class="fas fa-icon"></i>
  Button Text
</a>

<!-- Secondary Button -->
<button class="bg-gray-300 text-gray-700 px-8 py-4 rounded-lg 
              font-semibold hover:bg-gray-400 hover:scale-105 
              transition-all duration-300">
  <i class="fas fa-icon mr-2"></i>
  Secondary Action
</button>
```

**Classes**:
- `bg-gradient-to-r from-[color]-600 to-[color]-600`
- `text-white` for primary
- `px-8 py-4` padding
- `rounded-lg` corners (8px)
- `font-semibold` weight
- `hover:shadow-lg` shadow on hover
- `hover:scale-105` scale on hover
- `transition-all duration-300` animation
- `inline-flex items-center gap-2` for icon + text

---

### Form Inputs
**Usage**: Text input, search, filters

```html
<!-- Input Field -->
<div>
  <label class="block text-sm font-semibold text-gray-700 mb-2">
    <i class="fas fa-search mr-2 text-blue-600"></i>Search
  </label>
  <input type="text" 
         class="w-full px-4 py-3 border-2 border-gray-200 
                 rounded-lg focus:outline-none focus:border-blue-500 
                 focus:ring-2 focus:ring-blue-200 transition-colors"
         placeholder="Type here...">
</div>

<!-- Select Field -->
<select class="w-full px-4 py-3 border-2 border-gray-200 
              rounded-lg focus:outline-none focus:border-blue-500 
              focus:ring-2 focus:ring-blue-200 transition-colors">
  <option>Option 1</option>
  <option>Option 2</option>
</select>
```

**Classes**:
- `w-full` full width
- `px-4 py-3` padding
- `border-2 border-gray-200` border
- `rounded-lg` corners
- `focus:border-blue-500` focus border color
- `focus:ring-2 focus:ring-blue-200` focus ring
- `transition-colors` smooth color change

---

### Background Sections
**Usage**: Full-width sections with background colors

```html
<!-- Gradient Background Section -->
<section class="py-20 bg-gradient-to-br from-blue-50 to-indigo-100">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Content -->
  </div>
</section>

<!-- Solid Background Section -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Content -->
  </div>
</section>
```

**Classes**:
- `py-20` vertical padding
- `bg-gradient-to-br from-[color]-50 to-[color]-100`
- `bg-white` for solid white
- `px-4 sm:px-6 lg:px-8` responsive horizontal padding

---

### Badges & Tags
**Usage**: Status indicators, labels, counts

```html
<!-- Info Badge -->
<div class="inline-flex items-center gap-2 bg-blue-100 px-4 py-2 rounded-full mb-6">
  <i class="fas fa-fire text-orange-500"></i>
  <span class="text-sm font-semibold text-blue-700">Featured</span>
</div>

<!-- Verified Badge -->
<div class="flex items-center gap-1 text-green-600 text-sm font-semibold">
  <i class="fas fa-check-circle"></i>
  Verified
</div>

<!-- Results Counter -->
<p class="text-gray-700 font-semibold">
  <i class="fas fa-list-ul mr-2 text-blue-600"></i>
  Showing <span class="text-blue-600 font-bold">{{ count }}</span> items
</p>
```

---

### Icons
**Usage**: Visual indicators, navigation, actions

**Icon Sizing**:
- Headings: `text-3xl` to `text-7xl`
- Cards: `text-4xl`
- Buttons: `text-2xl`
- Badges: `text-2xl`
- Inline: `text-xl`

**Icon Coloring**:
```html
<!-- Colored Icons -->
<i class="fas fa-briefcase text-blue-600"></i>
<i class="fas fa-building text-green-600"></i>
<i class="fas fa-cogs text-purple-600"></i>
<i class="fas fa-star text-yellow-400"></i>
<i class="fas fa-fire text-orange-500"></i>
```

---

## Animation Reference

### Hover Effects
```css
/* Scale Animation */
hover:scale-105

/* Shadow Animation */
hover:shadow-2xl

/* Combined Effect */
hover:scale-105 hover:shadow-2xl

/* Transition Duration */
transition-all duration-300
```

### Usage Example
```html
<div class="shadow-lg hover:shadow-2xl hover:scale-105 transition-all duration-300">
  Content with smooth animations
</div>
```

---

## Typography

### Heading Sizes
```html
<!-- Page Title -->
<h1 class="text-5xl md:text-7xl font-bold text-gray-900">
  Main Title
</h1>

<!-- Section Title -->
<h2 class="text-4xl font-bold text-gray-900">
  Section Title
</h2>

<!-- Subsection Title -->
<h3 class="text-2xl font-bold text-gray-900">
  Subsection
</h3>

<!-- Card Title -->
<h3 class="text-xl font-bold text-gray-900">
  Card Title
</h3>
```

### Text Styles
```html
<!-- Primary Text -->
<p class="text-gray-900 leading-relaxed">Regular text</p>

<!-- Secondary Text -->
<p class="text-gray-600">Secondary information</p>

<!-- Muted Text -->
<p class="text-gray-500 text-sm">Small muted text</p>

<!-- Bold Accent -->
<span class="text-blue-600 font-bold">Important highlight</span>
```

---

## Spacing Guide

### Padding
```
px-4: 16px horizontal
px-6: 24px horizontal
px-8: 32px horizontal
py-3: 12px vertical
py-4: 16px vertical
py-6: 24px vertical
py-8: 32px vertical
py-10: 40px vertical
py-12: 48px vertical
py-16: 64px vertical
py-20: 80px vertical
```

### Margins
```
gap-2: 8px between items
gap-3: 12px between items
gap-4: 16px between items
gap-6: 24px between items
gap-8: 32px between items
mb-2: 8px margin bottom
mb-4: 16px margin bottom
mb-6: 24px margin bottom
mb-8: 32px margin bottom
```

---

## Responsive Breakpoints

```html
<!-- Mobile First -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <!-- 1 column on mobile, 2 on tablet, 3 on desktop -->
</div>

<!-- Text Sizes -->
<h1 class="text-2xl md:text-4xl lg:text-5xl">Responsive Text</h1>

<!-- Padding -->
<div class="px-4 sm:px-6 lg:px-8">Responsive padding</div>
```

---

## Common Patterns

### Hero Section
```html
<section class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-24">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center">
      <h1 class="text-5xl md:text-7xl font-bold mb-6">Title</h1>
      <p class="text-xl text-blue-100 mb-10">Subtitle</p>
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <button>Primary</button>
        <button>Secondary</button>
      </div>
    </div>
  </div>
</section>
```

### Stats Grid
```html
<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
  <div class="bg-white rounded-xl shadow-lg p-8 hover:shadow-2xl hover:scale-105">
    <div class="text-4xl font-bold text-blue-600 mb-2">0</div>
    <div class="text-gray-700 font-semibold">Stat Label</div>
  </div>
</div>
```

### Feature Cards
```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-8 
              hover:shadow-lg hover:scale-105 transition-all">
    <i class="fas fa-icon text-4xl text-blue-600 mb-4"></i>
    <h3 class="text-xl font-bold text-gray-900 mb-2">Feature</h3>
    <p class="text-gray-600">Description</p>
  </div>
</div>
```

---

## Color Usage Guide

| Color | Usage | Primary Shade |
|-------|-------|---------------|
| Blue | Backgrounds, primary actions | blue-600 |
| Indigo | Secondary actions, gradients | indigo-600 |
| Green | Success, positive, verified | green-600 |
| Purple | Alternative sections | purple-600 |
| Yellow | Featured, highlights | yellow-300/400 |
| Red | Destructive actions, alerts | red-600 |
| Gray | Text, neutral elements | gray-900/600 |

---

## Quick Copy-Paste Components

### Featured Badge
```html
<div class="inline-flex items-center gap-2 bg-blue-100 px-4 py-2 rounded-full">
  <i class="fas fa-star text-yellow-400"></i>
  <span class="text-sm font-semibold text-blue-700">Featured</span>
</div>
```

### Action Button
```html
<a href="#" class="inline-flex items-center gap-2 bg-gradient-to-r 
                   from-blue-600 to-indigo-600 text-white px-6 py-3 
                   rounded-lg font-semibold hover:shadow-lg hover:scale-105 
                   transition-all duration-300">
  <i class="fas fa-arrow-right"></i>
  View Details
</a>
```

### Info Card
```html
<div class="bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
  <p class="text-blue-900">
    <i class="fas fa-info-circle mr-2"></i>
    <strong>Info:</strong> Important information here.
  </p>
</div>
```

---

**Last Updated**: November 18, 2025  
**Platform**: Catanduanes Connect  
**Version**: 1.0 Complete Styling
