<script setup lang="ts">
const props = withDefaults(defineProps<{ name?: string }>(), { name: 'file' })

const paths: Record<string, string> = {
  home: 'M3 10l9-7 9 7M5 9v11h5v-6h4v6h5V9', work: 'M4 5h16v15H4zM8 5V3h8v2M8 10h8M8 14h8',
  idea: 'M9 18h6M10 21h4M8 14a6 6 0 1 1 8 0l-1 3H9z', book: 'M3 4h7l2 2 2-2h7v16h-7l-2 1-2-1H3zM12 6v15',
  meeting: 'M3 4h18v13H3zM12 17v4M8 21h8M7 8h10M7 12h6', settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2',
  search: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 15l6 6', plus: 'M12 4v16M4 12h16',
  arrow: 'M5 12h14M14 7l5 5-5 5', back: 'M19 12H5M10 7l-5 5 5 5', check: 'M5 12l4 4L19 6',
  circle: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18', spark: 'M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z',
  message: 'M4 4h16v12H9l-5 4zM8 8h8M8 12h5', file: 'M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6',
  link: 'M10 7l3-3a4 4 0 0 1 6 6l-3 3M14 17l-3 3a4 4 0 0 1-6-6l3-3M8 16l8-8',
  clock: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 7v5l3 2', close: 'M5 5l14 14M19 5L5 19',
  layers: 'M12 3l10 5-10 5L2 8zM2 12l10 5 10-5M2 16l10 5 10-5', server: 'M3 4h18v6H3zM3 14h18v6H3zM7 7h.1M7 17h.1',
  play: 'M7 4l13 8-13 8z', pause: 'M8 4v16M16 4v16', code: 'M8 6l-6 6 6 6M16 6l6 6-6 6M14 3l-4 18',
  history: 'M3 10a9 9 0 1 1 1 7M3 4v6h6M12 7v5l4 2', user: 'M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8M4 21v-3c0-6 16-6 16 0v3',
  flag: 'M5 22V3M5 3h14l-3 5 3 5H5', menu: 'M4 6h16M4 12h16M4 18h16',
  download: 'M12 3v12M7 10l5 5 5-5M4 16v5h16v-5', shield: 'M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6zM8 12l3 3 5-6',
  refresh: 'M20 7a9 9 0 1 0 1 9M20 2v5h-5', edit: 'M4 16l-1 5 5-1L20 8l-4-4zM13 7l4 4',
  eye: 'M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
}
</script>

<template>
  <svg class="gz-icon" viewBox="0 0 24 24" aria-hidden="true">
    <path :d="paths[props.name] ?? paths.file" />
  </svg>
</template>
