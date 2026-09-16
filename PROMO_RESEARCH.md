# Property Film Design Notes

ASTRA's photo-film editor converts supplied images into a restrained property-first
sequence. It does not synthesize unphotographed rooms, amenities, people, or views.

## Implemented editorial rules

- Composition score combines brightness suitability, visual entropy, symmetry, and architectural line evidence.
- The strongest composition opens; a separate strong composition closes when enough photos are available.
- Every supplied photo appears once. Each receives a slow, stable movement rather than a simulated impossible walkthrough.
- Cross-motion transitions are only selected for visually compatible consecutive frames; otherwise the editor uses a fade.
- The visual finish is warm, gentle, and detailed rather than a heavy movie filter.

## Sources reviewed

- Zhang et al., *What Makes a Good Image? Airbnb Demand Analytics Leveraging Interpretable Image Features* (composition, color, and figure-ground attributes).
- Professional luxury-listing editorial guidance emphasizing property-first sequencing, restrained branding, wide/medium/detail hierarchy, and transitions that respect real spatial relationships.
