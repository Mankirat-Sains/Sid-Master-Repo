/**
 * Composable for making panels resizable
 */
export const useResizable = (direction: 'vertical' | 'horizontal') => {
  const isResizing = ref(false)
  const startPos = ref(0)
  const startSize = ref(0)

  function onMouseDown(e: MouseEvent, currentSize: number) {
    isResizing.value = true
    startPos.value = direction === 'vertical' ? e.clientY : e.clientX
    startSize.value = currentSize
    e.preventDefault()
  }

  function onMouseMove(e: MouseEvent, callback: (newSize: number) => void) {
    if (!isResizing.value) return

    const currentPos = direction === 'vertical' ? e.clientY : e.clientX
    const delta = currentPos - startPos.value
    const newSize = direction === 'vertical' 
      ? startSize.value + delta 
      : startSize.value - delta
    
    callback(newSize)
  }

  function onMouseUp() {
    isResizing.value = false
  }

  return {
    isResizing,
    onMouseDown,
    onMouseMove,
    onMouseUp
  }
}

