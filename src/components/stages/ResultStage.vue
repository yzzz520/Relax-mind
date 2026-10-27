<!-- 结果页容器：组织播放器占位、情绪雷达、标签云、疗愈语与操作按钮。 -->
<!-- 输入 capsule，输出 restart 事件。 -->
<script setup>
import EmotionRadar from '../EmotionRadar.vue'
import Radar from '../fx/Radar.vue'
import HealingComment from '../HealingComment.vue'
import KeywordCloud from '../KeywordCloud.vue'
import MusicPlayer from '../player/MusicPlayer.vue'

const props = defineProps({
  capsule: {
    type: Object,
    required: true,
  },
  saveState: {
    type: String,
    default: 'idle',
  },
})

const emit = defineEmits(['restart'])
</script>

<template>
  <section
    class="result-stage"
    :style="{ '--accent': capsule.palette[0] }"
    aria-labelledby="result-title"
  >
    <h1 id="result-title" class="visually-hidden">情绪胶囊结果</h1>

    <div class="result-grid">
      <div class="result-left">
        <MusicPlayer :track="capsule.music" :palette="capsule.palette" />
        <HealingComment
          :comment="capsule.comment"
          :palette="capsule.palette"
        />
      </div>

      <div class="result-right">
        <section class="result-panel radar-panel">
          <div class="radar-fx-layer" aria-hidden="true">
            <Radar
              :color="capsule.palette[0]"
              :speed="0.5"
              :ring-count="5"
              :spoke-count="8"
              :targets="0"
              :mouse-interaction="false"
              :opacity="0.45"
            />
          </div>
          <header class="panel-heading">
            <h2>情绪 DNA</h2>
            <span>八维图谱</span>
          </header>
          <div class="radar-data-layer">
            <EmotionRadar
              :emotions="capsule.emotions"
              :palette="capsule.palette"
            />
          </div>
        </section>

        <section class="result-panel cloud-panel">
          <p class="soft-heading">此刻的你</p>
          <KeywordCloud :labels="capsule.fineLabels" />
        </section>
      </div>
    </div>

    <p
      v-if="saveState !== 'idle'"
      class="save-state"
      :class="`is-${saveState}`"
      role="status"
    >
      {{
        saveState === 'saving'
          ? '正在保存记录'
          : saveState === 'saved'
            ? '已保存'
            : '已生成，但记录未保存'
      }}
    </p>

    <div class="result-actions">
      <button class="secondary-button" type="button" @click="emit('restart')">
        再来一个
      </button>
      <button class="primary-button" type="button" disabled>
        保存为情绪卡片
      </button>
    </div>
  </section>
</template>

<style scoped>
.result-stage {
  position: relative;
  z-index: 1;
  min-height: 100dvh;
  padding: 96px 24px 32px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
  white-space: nowrap;
}

.result-grid {
  display: grid; grid-template-columns: minmax(320px, 0.85fr) 1.15fr;
  gap: 24px; width: 100%; max-width: var(--result-maxw);
  margin: 0 auto; align-items: start;
}

.result-left,
.result-right {
  display: grid; gap: 20px; min-width: 0;
}

.result-right { grid-template-rows: auto auto; gap: 16px; }
.cloud-panel { min-height: 140px; }

.soft-heading {
  margin: 0 0 16px; color: rgba(255, 255, 255, 0.55);
  font-size: 12px; letter-spacing: 0.08em;
}

.result-panel {
  min-width: 0; padding: var(--panel-padding);
  border: 1px solid var(--glass-border); border-radius: var(--radius-card);
  background: var(--glass-bg);
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.035);
  backdrop-filter: blur(var(--glass-blur));
}

.radar-panel { position: relative; overflow: hidden; isolation: isolate; }
.radar-fx-layer { position: absolute; z-index: 0; inset: 0; pointer-events: none; }
.radar-data-layer { position: relative; z-index: 1; opacity: 0.85; }

.panel-heading {
  position: relative; z-index: 2; display: flex; align-items: center;
  justify-content: space-between; gap: 14px; margin-bottom: 8px;
}

.panel-heading h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 400;
  letter-spacing: 0.1em;
}

.panel-heading span {
  color: var(--text-secondary);
  font-size: 10px;
  letter-spacing: 0.12em;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  width: min(100%, var(--result-maxw));
  margin: 28px auto 0;
}

.save-state {
  width: min(100%, var(--result-maxw));
  margin: 18px auto -14px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-align: center;
}

.save-state.is-saved { color: rgba(143, 227, 207, 0.66); }
.save-state.is-failed { color: rgba(255, 190, 150, 0.62); }

.secondary-button,
.primary-button {
  min-height: 46px;
  padding: 0 22px;
  border-radius: 10px;
  font-size: 13px;
  letter-spacing: 0.05em;
}

.secondary-button {
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
}

.secondary-button:hover {
  background: rgba(255, 255, 255, 0.09);
}

.primary-button {
  border: 1px solid color-mix(in srgb, var(--accent) 48%, transparent);
  background: color-mix(in srgb, var(--accent) 18%, transparent);
  color: rgba(255, 255, 255, 0.82);
}

.primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

@media (max-width: 1023px) {
  .result-stage {
    padding: 76px 24px 28px;
  }

  .result-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .result-left,
  .result-right {
    gap: 16px;
  }

  .result-panel {
    padding: 16px;
  }

  .panel-heading {
    margin-bottom: 4px;
  }
}

@media (max-width: 560px) {
  .result-stage {
    padding: 76px 4vw 28px;
  }

  .result-grid {
    gap: 16px;
  }

  .result-actions {
    flex-direction: column;
    margin-top: 20px;
  }

  .secondary-button,
  .primary-button {
    width: 100%;
  }
}
</style>
