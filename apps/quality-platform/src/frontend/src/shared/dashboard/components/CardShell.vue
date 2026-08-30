<script setup lang="ts">
defineProps<{
  anchorId?: string
  title: string
  description?: string
  removable?: boolean
  editable?: boolean
}>()

const emit = defineEmits<{ remove: []; edit: [] }>()
</script>

<template>
  <article :id="anchorId" class="card-shell">
    <header class="card-header">
      <span
        class="card-drag-handle"
        role="button"
        tabindex="0"
        :aria-label="`拖动卡片：${title}`"
        title="按住拖动卡片"
      >
        <span aria-hidden="true">⠿</span>
      </span>
      <div>
        <p v-if="description" class="card-description">{{ description }}</p>
        <h3>{{ title }}</h3>
      </div>
      <div class="card-actions">
        <slot name="actions" />
        <button
          v-if="editable"
          class="icon-button"
          type="button"
          :aria-label="`编辑卡片：${title}`"
          title="编辑卡片"
          @click="emit('edit')"
        >
          ✎
        </button>
        <button
          v-if="removable"
          class="icon-button"
          type="button"
          :aria-label="`删除卡片：${title}`"
          @click="emit('remove')"
        >
          ×
        </button>
      </div>
    </header>

    <div class="card-content">
      <slot />
    </div>

    <footer v-if="$slots.footer" class="card-footer">
      <slot name="footer" />
    </footer>
  </article>
</template>

<style scoped>
.card-shell {
  display: grid;
  height: 100%;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  min-height: 66px;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 13px 14px 10px;
  border-bottom: 1px solid var(--color-line-subtle);
}

.card-drag-handle {
  display: grid;
  width: 28px;
  height: 30px;
  place-items: center;
  border: 0;
  background: transparent;
  color: #8290a0;
  cursor: grab;
  font-size: 18px;
  line-height: 1;
}

.card-drag-handle:active {
  cursor: grabbing;
}

.card-header h3,
.card-description {
  margin: 0;
}

.card-header h3 {
  margin-top: 3px;
  font-size: 15px;
  letter-spacing: -0.01em;
}

.card-description {
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 750;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-button {
  display: grid;
  width: 29px;
  height: 29px;
  place-items: center;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  background: white;
  color: var(--color-muted);
  font-size: 18px;
  line-height: 1;
}

.icon-button:hover {
  border-color: #9eb2c9;
  color: var(--color-primary);
}

.card-content {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding: 10px 14px 12px;
}

.card-footer {
  padding: 9px 14px;
  border-top: 1px solid var(--color-line-subtle);
  background: var(--color-surface-subtle);
}
</style>
