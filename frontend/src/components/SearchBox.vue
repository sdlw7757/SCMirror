<template>
  <div class="relative">
    <svg viewBox="0 0 24 24" class="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
    <input
      :value="modelValue"
      @input="onInput"
      type="text"
      inputmode="search"
      placeholder="搜索标题 / build 号 / SHA256 片段 / KB 编号，例如输入 10 查看全部 Windows 10…"
      class="input-dark pl-11 pr-28 py-3 !rounded-2xl shadow-card"
    />
    <span v-if="modelValue" class="absolute right-3 top-1/2 -translate-y-1/2">
      <button
        class="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-400 transition hover:text-slate-200"
        @click="clear"
      >
        清空
      </button>
    </span>
  </div>
</template>

<script setup>
defineProps({ modelValue: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue'])
function onInput(e) {
  emit('update:modelValue', e.target.value)
}
function clear() {
  emit('update:modelValue', '')
}
</script>
