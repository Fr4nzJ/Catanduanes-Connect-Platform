# Business Registration Page - Visual Reference Guide

## Page Layout

```
┌─────────────────────────────────────────────────┐
│  HEADER (Blue Gradient Background)              │
│  🏪 Register Your Business                      │
│  Join thousands of businesses...               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                                                 │
│  FORM CONTAINER (White with Shadow)            │
│  ┌────────────────────────────────────────────┐│
│  │ ① BUSINESS INFORMATION                    ││
│  │ [Business Name Input]                     ││
│  │ [Category Dropdown]                       ││
│  │ [Description Textarea]                    ││
│  │ [Address Input] [Pin Location Button]     ││
│  │ [Phone Input] [Email Input]               ││
│  │ [Website Input]                           ││
│  └────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────┐│
│  │ ② VERIFICATION DOCUMENTS                  ││
│  │ ⚠️  Verification Required Info Box        ││
│  │ [Permit Number Input]                     ││
│  │ [File Upload Drag-Drop Area]              ││
│  └────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────┐│
│  │ [Terms & Conditions Checkbox]              ││
│  │ [Cancel Button] [Register Button]         ││
│  └────────────────────────────────────────────┘│
│                                                 │
└─────────────────────────────────────────────────┘

                    [AI Bubble]
                    (Bottom Right)
```

## AI Bubble States

### Closed State
```
┌──────────┐
│  ✨      │
│          │ (70x70px, Purple Gradient)
│          │ Hover → Scale 1.1
└──────────┘
```

### Open State
```
┌──────────────────────────────┐
│ ✨ AI Assistant      [✕]     │ (Header - Purple Gradient)
├──────────────────────────────┤
│ How can I help?              │
│                              │
│ [EN] [TL] [BL]  (Language)   │
│                              │
│ [📝 Improve Description]     │ (Primary)
│ [💡 Registration Tips]       │ (Secondary)
│ [📋 Review Business Info]    │ (Secondary)
│                              │
└──────────────────────────────┘
(350px wide, Animated slide-up)
```

### Processing State
```
┌──────────────────────────────┐
│ ✏️  Improving Description     │
├──────────────────────────────┤
│ Analyzing and improving...   │ (Pulsing)
│ (Circle pulsing)             │
└──────────────────────────────┘
```

### Response State
```
┌──────────────────────────────┐
│ ✨ AI Suggestion     [✕]     │
├──────────────────────────────┤
│ [AI-generated response text] │
│ [scrollable content]         │
│                              │
└──────────────────────────────┘
```

## Color Scheme

### Primary Gradient
```
From: #667eea (Indigo Blue)
To:   #764ba2 (Purple)
```

### Text Colors
- Primary: #333333
- Secondary: #666666
- Muted: #999999
- Error: #d32f2f
- Success: #22c55e

### Background Colors
- Page: Linear gradient (blue-50 → white → indigo-50)
- Form: White (#ffffff)
- Alert: Blue-50/Blue-200 border
- Success: Green-50/Green-200 border
- Warning: Amber-50/Amber-200 border

## Form Input Styling

```
Focus State:
┌────────────────────────┐
│ Input Text             │ Border: #667eea (2px)
│                        │ Ring: Blue-500
└────────────────────────┘

Error State:
┌────────────────────────┐
│ Input Text             │ Border: Red (2px)
│ ⚠️ Error message       │ Text: Red
└────────────────────────┘

Placeholder:
┌────────────────────────┐
│ placeholder text...    │ Color: Gray-400
└────────────────────────┘
```

## Button Styling

### Primary Button (Register)
```
[Register Business 🏢]
- Background: Gradient (Blue-600 → Indigo-600)
- Text: White
- Hover: Scale 1.05, Shadow
- Padding: 12px 24px
```

### Secondary Button (Cancel)
```
[Cancel ←]
- Background: Gray-200
- Text: Gray-800
- Hover: Gray-300
- Padding: 12px 24px
```

### AI Buttons
```
[📝 Improve Description]
- Background: Gradient (Primary button style)
- Text: White
- Width: 100%
- Hover: Darker gradient
```

## Input Field Styling

```
┌─────────────────────────────────────────┐
│ 🏢 Business Name (Label Icon)          │
│ ┌───────────────────────────────────────┤
│ │ Enter your business name              │ (Placeholder)
│ └───────────────────────────────────────┤
│ ⓘ Minimum 10 characters (Help text)    │
└─────────────────────────────────────────┘

Default: Border 2px Gray-200
Focus: Border 2px Blue-500, Ring Blue-500
Error: Border 2px Red, Ring Red-500
```

## File Upload Area

```
Default State:
┌─────────────────────────────────────┐
│         ☁️  (Large Icon)            │
│  Click to upload or drag and drop   │
│  PDF, JPG, JPEG, or PNG only       │
└─────────────────────────────────────┘
Border: Dashed Gray-300

Hover State:
┌─────────────────────────────────────┐  Border: Dashed Blue-500
│         ☁️                          │  Background: Blue-50
│  Click to upload or drag and drop   │
│  PDF, JPG, JPEG, or PNG only       │
└─────────────────────────────────────┘

File Uploaded State:
┌─────────────────────────────────────────────┐
│ 📄 document.pdf          [✕]               │
│ ✓ Ready to upload                          │
└─────────────────────────────────────────────┘
Background: Green-50, Border: Green-200
```

## Modal (Location Picker)

```
┌──────────────────────────────────────┐
│ 📍 Drop the pin on exact location [✕]│ (Header)
├──────────────────────────────────────┤
│                                      │
│  [MAP DISPLAY - 384px height]        │
│                                      │
├──────────────────────────────────────┤
│     [Center on me] [Confirm]        │ (Buttons)
└──────────────────────────────────────┘
```

## AI Command Examples

### Command 1: Improve Description
**Input:**
```
Description: "We sell clothes"
Category: "Retail - Fashion"
Language: "English"
```

**Output:**
```
"We are a premier fashion retail destination specializing in 
contemporary clothing for men and women. Our curated collection 
features high-quality pieces from emerging designers and established 
brands, offering styles ranging from casual everyday wear to elegant 
evening attire. With personalized styling services and a commitment 
to customer satisfaction, we help you express your unique style."
```

### Command 2: Registration Tips
**Input:**
```
Category: "Restaurant - Dining"
Language: "English"
```

**Output:**
```
1. Highlight Menu Diversity - Clearly describe your signature dishes 
and cuisine type to attract food enthusiasts.

2. Emphasize Location & Ambiance - Include details about your dining 
experience, seating capacity, and special features like outdoor seating.

3. Avoid Common Mistakes - Don't use generic descriptions; be specific 
about what makes your restaurant unique.

4. Add Operating Hours & Services - Clearly state hours, accept 
reservations status, and delivery options.

5. Professional Presentation - Use high-quality descriptions and update 
regularly to maintain credibility.
```

### Command 3: Review Business Info
**Input:**
```
Name: "Fresh Catch Seafood"
Description: "Quality seafood restaurant..."
Category: "Restaurant - Dining"
Language: "English"
```

**Output:**
```
Overall Quality: 8/10

Strengths:
- Clear business focus on seafood
- Professional description structure
- Good category selection

Areas for Improvement:
- Add specific signature dishes
- Include price range information
- Mention any certifications or awards

Suggestions:
- Describe the dining experience
- Add information about sourcing practices
- Include reservation information

Ready for Listing: Yes - With minor enhancements
```

## Animations

### Slide-Up (Bubble Appears)
```
From: Y: +20px, Opacity: 0
To:   Y: 0, Opacity: 1
Duration: 0.3s ease
```

### Pulse (Processing)
```
0%:   Scale 1.0
50%:  Scale 1.05
100%: Scale 1.0
Duration: 1.5s ease-in-out infinite
```

### Hover Scale (Buttons/Circle)
```
From: Scale 1.0
To:   Scale 1.05
Duration: 0.2s ease
```

### Focus Outline
```
Ring: 2px solid #667eea
Ring-Offset: 2px
```

## Responsive Breakpoints

- **Mobile** (< 640px): Single column, full-width inputs
- **Tablet** (640px - 1024px): Two-column layout where applicable
- **Desktop** (> 1024px): Full two-column layout, optimal spacing

## Loading States

### AI Processing
```
✨ [Feature Name]
Loading... (with pulsing animation)
```

### Error State
```
⚠️ Error
Unable to process. Please try again.
```

### Success State
```
✨ AI Suggestion
[Full AI-generated response displayed]
```
