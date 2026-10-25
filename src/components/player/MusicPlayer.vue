<!-- 音乐播放器：播放循环曲目并驱动黑胶与粒子动效。 -->
<!-- 输入 track、palette，输出播放状态与音频错误提示。 -->
<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { QUADRANT_LABELS } from '../../data/musicLibrary'
import Particles from '../fx/Particles.vue'
import VinylHalo from '../fx/VinylHalo.vue'

const props = defineProps({
  track: {
    type: Object,
    required: true,
  },
  palette: {
    type: Array,
    default: () => ['#7C5CFF', '#FF8FB1'],
  },
})

const audio = ref(null)
const isPlaying = ref(false)
const isUnavailable = ref(false)

const quadrantLabel = computed(
  () => QUADRANT_LABELS[props.track.quadrant] ?? '',
)
const particleColors = computed(() => [props.palette[0]])

async function togglePlayback() {
  const audioElement = audio.value

  if (!audioElement || isUnavailable.value) {
    return
  }

  if (!audioElement.paused) {
    audioElement.pause()
    return
  }

  try {
    await audioElement.play()
  } catch {
    isUnavailable.value = true
    isPlaying.value = false
  }
}

function handleAudioError() {
  isUnavailable.value = true
  isPlaying.value = false
}

function handleTrackChange() {
  const audioElement = audio.value

  if (audioElement) {
    audioElement.pause()
    audioElement.currentTime = 0
  }

  isPlaying.value = false
  isUnavailable.value = false
}

watch(() => props.track.id, handleTrackChange)

onBeforeUnmount(() => {
  if (audio.value) {
    audio.value.pause()
    audio.value.currentTime = 0
  }

})

defineExpose({
  audio,
})
</script>

<template>
  <article
    class="player-card"
    :style="{ '--accent': palette[0], '--accent-secondary': palette[1] }"
  >
    <header class="player-heading">
      <span>音乐胶囊</span>
      <span class="loop-badge">循环 · Lo-fi</span>
    </header>

    <div class="disc-shell">
      <div class="disc-field">
        <div class="disc-halo" aria-hidden="true">
          <VinylHalo :is-playing="isPlaying" />
        </div>
        <div class="disc" :class="{ playing: isPlaying }">
          <div class="disc-center">
            <Particles
              :particle-count="800"
              :particle-base-size="1.2"
              :speed="0.3"
              :particle-colors="particleColors"
            />
          </div>
        </div>
        <div class="halo-foreground" aria-hidden="true">
          <span class="halo-bokeh bokeh-a"></span>
          <span class="halo-bokeh bokeh-b"></span>
          <span class="halo-bokeh bokeh-c"></span>
          <span class="halo-bokeh bokeh-d"></span>
        </div>
      </div>
    </div>

    <div class="track-copy">
      <h2>{{ track.title }}</h2>
      <p class="track-meta">
        <span>{{ track.artist }}</span>
        <span v-if="track.artist && quadrantLabel" aria-hidden="true">·</span>
        <span>{{ quadrantLabel }}</span>
      </p>
    </div>

    <button
      class="play-button"
      type="button"
      :disabled="isUnavailable"
      :aria-label="isPlaying ? '暂停' : '播放'"
      @click="togglePlayback"
    >
      <span class="play-icon" :class="{ paused: isPlaying }"></span>
    </button>

    <p v-if="isUnavailable" class="audio-error">音频不可用</p>
    <span v-else class="audio-status" aria-hidden="true"></span>

    <audio
      ref="audio"
      class="audio-element"
      :src="track.file"
      loop
      preload="metadata"
      @play="isPlaying = true"
      @pause="isPlaying = false"
      @error="handleAudioError"
    ></audio>
  </article>
</template>

<style scoped src="../../assets/styles/music-player.css"></style>
