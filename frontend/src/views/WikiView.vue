<template>
  <div class="mx-auto max-w-4xl px-4 pb-16 md:px-6">
    <div class="pt-8 md:pt-12">
      <nav class="mb-3 flex items-center gap-1.5 text-xs text-slate-500">
        <RouterLink to="/" class="transition hover:text-cyan-300">首页</RouterLink>
        <span>/</span>
        <span class="text-slate-400">知识库</span>
      </nav>

      <div class="mb-6">
        <h1 class="text-2xl font-extrabold tracking-tight md:text-3xl">
          <span class="glow-text">Windows 镜像知识库</span>
        </h1>
        <p class="mt-2 text-sm text-slate-400">常见概念、版本区分与校验方法，帮助你正确选择与验证官方原版镜像。</p>
      </div>

      <div class="space-y-4">
        <article v-for="a in articles" :key="a.title" class="glass p-5">
          <h2 class="mb-2 flex items-center gap-2 text-base font-bold text-slate-100">
            <span class="h-4 w-1 rounded bg-cyan-400"></span>{{ a.title }}
          </h2>
          <p v-for="(p, i) in a.paras" :key="i" class="mb-2 text-sm leading-relaxed text-slate-400 last:mb-0">{{ p }}</p>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup>
const articles = [
  {
    title: '消费者版（零售）与商业版（批量）的区别',
    paras: [
      '商业版（business）集成：专业版、企业版、教育版、专业工作站版、专业教育版；',
      '消费者版（consumer）集成：家庭版、专业版、教育版、家庭单语言版、专业工作站版、专业教育版。',
      '若只需专业版，两个版本均可；若需要企业版（Enterprise），请选择商业版。',
    ],
  },
  {
    title: '32 位、64 位与 ARM64 如何选择',
    paras: [
      '64 位（x64）是当前主流，绝大多数新电脑都适用，无脑选择 64 位即可；',
      '32 位（x86）仅用于非常老的设备；ARM64 仅在你明确知道设备是 ARM 处理器时选择。',
    ],
  },
  {
    title: '如何校验官方原版镜像',
    paras: [
      '微软发布系统文件时会同时公布其哈希值（MD5 / SHA1 / SHA256），哈希值相当于文件的“身份证”。',
      '在【哈希校验工具】页面选择文件，即可在本地计算其 SHA256，与本站聚合库中各数据源公布的哈希逐一比对；',
      '哈希完全一致，说明文件来自官方原版、未被改动或植入内容。',
    ],
  },
  {
    title: '生命周期 / 支持状态说明',
    paras: [
      '【支持中】表示该系统仍在微软支持周期内，可获得安全更新；',
      '【已停止支持】表示微软已终止对该版本的技术支持与安全更新，建议仅在了解风险的前提下用于学习研究。',
    ],
  },
  {
    title: '本站收录数据的原则',
    paras: [
      '本站以 SHA256 为全局唯一主键，将同一镜像的多个数据源聚为一条主数据，并独立保留各站原始文件名、哈希、下载链接与采集时间；',
      '不做任何安全评级，仅在聚合基础上提供元信息对照，下载前请务必自行校验哈希。',
      '本站仅聚合整理网络公开元信息与下载链接，不存储镜像文件，请使用正版系统。',
    ],
  },
]
</script>
