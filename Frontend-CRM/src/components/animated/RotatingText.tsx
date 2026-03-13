import React, { useState, useEffect, useRef } from 'react'

interface RotatingTextProps {
  items: string[]
  intervalMs?: number
  className?: string
}

// Color palette for rotating text (similar to Slack's gradient colors)
const TEXT_COLORS = [
  '#168AAD', // Dizzaroo blue-green
  '#1E73BE', // Dizzaroo deep blue
  '#76C893', // Dizzaroo soft green
  '#4BA8C5', // Dizzaroo blue-green light
  '#5BA374', // Dizzaroo soft green dark
  '#4A9FE8', // Dizzaroo deep blue light
]

export const RotatingText: React.FC<RotatingTextProps> = ({ 
  items, 
  intervalMs = 4000,
  className = ''
}) => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isAnimating, setIsAnimating] = useState(false)
  const containerRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (items.length <= 1) return

    const interval = setInterval(() => {
      setIsAnimating(true)
      
      // After slide animation completes, change to next item
      setTimeout(() => {
        setCurrentIndex((prevIndex) => (prevIndex + 1) % items.length)
        // Small delay before resetting animation state to ensure smooth transition
        setTimeout(() => {
          setIsAnimating(false)
        }, 50)
      }, 600) // Half of transition duration (1200ms)
    }, intervalMs)

    return () => clearInterval(interval)
  }, [items.length, intervalMs])

  if (items.length === 0) return null
  if (items.length === 1) return <span className={className}>{items[0]}</span>

  // Calculate max width to prevent layout shift
  const maxWidth = Math.max(...items.map(item => item.length)) * 0.7 + 'em'
  
  // Get color for current and next item
  const currentColor = TEXT_COLORS[currentIndex % TEXT_COLORS.length]
  const nextIndex = (currentIndex + 1) % items.length
  const nextColor = TEXT_COLORS[nextIndex % TEXT_COLORS.length]

  return (
    <span 
      ref={containerRef}
      className={`relative inline-block ${className}`}
      style={{ 
        minWidth: maxWidth,
        height: '1.2em',
        verticalAlign: 'bottom',
        display: 'inline-block',
        overflow: 'hidden',
        lineHeight: '1.2em',
        position: 'relative'
      }}
    >
      {/* Invisible spacer to maintain layout */}
      <span className="invisible whitespace-nowrap" aria-hidden="true" style={{ display: 'inline-block' }}>
        {items[currentIndex]}
      </span>
      
      {/* Current text - slides up and fades out */}
      <span
        className={`absolute left-0 whitespace-nowrap ${
          isAnimating 
            ? 'opacity-0 -translate-y-full' 
            : 'opacity-100 translate-y-0'
        }`}
        style={{ 
          top: 0,
          color: currentColor,
          willChange: 'transform, opacity, color',
          backfaceVisibility: 'hidden',
          WebkitBackfaceVisibility: 'hidden',
          pointerEvents: 'none',
          transition: 'transform 1200ms cubic-bezier(0.25, 0.46, 0.45, 0.94), opacity 1200ms cubic-bezier(0.25, 0.46, 0.45, 0.94), color 1200ms cubic-bezier(0.25, 0.46, 0.45, 0.94)',
          transform: isAnimating ? 'translateY(-100%)' : 'translateY(0)'
        }}
      >
        {items[currentIndex]}
      </span>
      
      {/* Next text - slides up from below and fades in */}
      <span
        className={`absolute left-0 whitespace-nowrap ${
          isAnimating 
            ? 'opacity-100 translate-y-0' 
            : 'opacity-0 translate-y-full'
        }`}
        style={{ 
          top: 0,
          color: nextColor,
          willChange: 'transform, opacity, color',
          backfaceVisibility: 'hidden',
          WebkitBackfaceVisibility: 'hidden',
          pointerEvents: 'none',
          transition: 'transform 1200ms cubic-bezier(0.25, 0.46, 0.45, 0.94), opacity 1200ms cubic-bezier(0.25, 0.46, 0.45, 0.94), color 1200ms cubic-bezier(0.25, 0.46, 0.45, 0.94)',
          transform: isAnimating ? 'translateY(0)' : 'translateY(100%)'
        }}
      >
        {items[nextIndex]}
      </span>
    </span>
  )
}

export default RotatingText

