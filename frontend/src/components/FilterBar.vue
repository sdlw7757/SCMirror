<template>
  <div class="glass p-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2 text-sm text-slate-300">
        <svg viewBox="0 0 24 24" class="h-4 w-4 text-cyan-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <path d="M3 6h18M6 12h12M10 18h4" />
        </svg>
        高级筛选
      </div>
      <div class="flex items-center gap-3">
        <button v-if="hasActive" class="text-xs text-slate-400 transition hover:text-cyan-300" @click="reset">重置</button>
        <button class="flex items-center gap-1 text-xs text-slate-400 transition hover:text-cyan-300 md:hidden" @click="open = !open">
          {{ open ? '收起' : '展开' }}
          <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" :class="open ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m6 9 6 6 6-6" />
          </svg>
        </button>
      </div>
    </div>

    <div class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4" :class="open ? '' : 'hidden md:grid'">
      <div>
        <label class="mb-1 block text-xs text-slate-500">系统分类</label>
        <select :value="modelValue.category" @change="set('category', $event.target.value)" class="input-dark">
          <option value="all">全部分类</option>
          <option v-for="c in categories" :key="c.key" :value="c.key">{{ c.name }}</option>
        </select>
      </div>
      <div>
        <label class="mb-1 block text-xs text-slate-500">架构</label>
        <select :value="modelValue.arch" @change="set('arch', $event.target.value)" class="input-dark">
          <option value="all">全部架构</option>
          <option value="x64">x64</option>
          <option value="x86">x86</option>
          <option value="arm64">ARM64</option>
        </select>
      </div>
      <div>
        <label class="mb-1 block text-xs text-slate-500">零售 / 批量</label>
        <select :value="modelValue.type" @change="set('type', $event.target.value)" class="input-dark">
          <option value="all">全部</option>
          <option value="consumer">消费者版（零售）</option>
          <option value="business">商业版（批量）</option>
        </select>
      </div>
      <div>
        <label class="mb-1 block text-xs text-slate-500">支持状态</label>
        <select :value="modelValue.lifecycle" @change="set('lifecycle', $event.target.value)" class="input-dark">
          <option value="all">全部</option>
          <option value="supported">支持中</option>
          <option value="ended">已停止支持</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store } from '../store'

const props = defineProps({ modelValue: { type: Object, required: true } })
const emit = defineEmits(['update:modelValue'])
const open = ref(false)
const categories = computed(() => store.data?.categories || [])

const hasActive = computed(() => props.modelValue.category !== 'all' || props.modelValue.arch !== 'all' || props.modelValue.type !== 'all' || props.modelValue.lifecycle !== 'all')

function set(key, val) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}
function reset() {
  emit('update:modelValue', { category: 'all', arch: 'all', type: 'all', lifecycle: 'all' })
}
</script>
