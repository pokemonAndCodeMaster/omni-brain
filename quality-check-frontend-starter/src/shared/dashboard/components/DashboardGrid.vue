<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { GridStack } from 'gridstack'
import type { GridStackNode } from 'gridstack'
import CardShell from '@/shared/dashboard/components/CardShell.vue'
import type { DashboardCard, GridPosition } from '@/shared/dashboard/types/dashboard'

const props = defineProps<{
  cards: DashboardCard[]
  editMode: boolean
}>()

const emit = defineEmits<{
  layoutChange: [layouts: Array<{ id: string; layout: GridPosition }>]
  remove: [id: string]
  duplicate: [id: string]
}>()

const root = ref<HTMLElement | null>(null)
let grid: GridStack | null = null

function emitLayout(items: GridStackNode[]) {
  emit(
    'layoutChange',
    items.flatMap((item) => {
      const id = item.el?.getAttribute('data-card-id')
      if (!id) return []
      return [
        {
          id,
          layout: {
            x: item.x ?? 0,
            y: item.y ?? 0,
            w: item.w ?? 4,
            h: item.h ?? 3,
          },
        },
      ]
    }),
  )
}

function makeNewWidgets() {
  if (!grid || !root.value) return
  root.value.querySelectorAll<HTMLElement>('.grid-stack-item').forEach((element) => {
    const maybeGridItem = element as HTMLElement & { gridstackNode?: GridStackNode }
    if (!maybeGridItem.gridstackNode) grid?.makeWidget(element)
  })
}

function removeCard(id: string) {
  const element = root.value?.querySelector<HTMLElement>(`[data-card-id="${id}"]`)
  if (grid && element) grid.removeWidget(element, false)
  emit('remove', id)
}

onMounted(() => {
  grid = GridStack.init(
    {
      column: 12,
      cellHeight: 78,
      margin: 10,
      float: true,
      disableDrag: !props.editMode,
      disableResize: !props.editMode,
      minRow: 1,
    },
    root.value ?? undefined,
  )

  grid.on('change', (_event, items) => emitLayout(items))
})

watch(
  () => props.editMode,
  (enabled) => {
    grid?.enableMove(enabled)
    grid?.enableResize(enabled)
  },
)

watch(
  () => props.cards.map((card) => card.id),
  async () => {
    await nextTick()
    makeNewWidgets()
  },
)

onBeforeUnmount(() => {
  grid?.destroy(false)
})
</script>

<template>
  <div ref="root" class="grid-stack" :class="{ 'is-editing': editMode }">
    <div
      v-for="card in cards"
      :key="card.id"
      class="grid-stack-item"
      :data-card-id="card.id"
      :gs-x="card.layout.x"
      :gs-y="card.layout.y"
      :gs-w="card.layout.w"
      :gs-h="card.layout.h"
      :gs-min-w="2"
      :gs-min-h="2"
    >
      <div class="grid-stack-item-content">
        <CardShell
          :card="card"
          :edit-mode="editMode"
          @remove="removeCard"
          @duplicate="emit('duplicate', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid-stack {
  min-height: 360px;
}

.grid-stack.is-editing {
  border-radius: var(--radius-md);
  background-image:
    linear-gradient(to right, rgb(37 87 214 / 6%) 1px, transparent 1px),
    linear-gradient(to bottom, rgb(37 87 214 / 6%) 1px, transparent 1px);
  background-size: calc(100% / 12) 78px;
}

.grid-stack-item-content {
  inset: 0 !important;
  overflow: visible !important;
}
</style>
