<template>
  <v-btn class="mb-4" prepend-icon="mdi-reload" @click="getGitDiff">
    再読み込み
  </v-btn>
</template>

<script setup lang="ts">
const props = defineProps({
  contentSetter: {
    type: Function,
    default: (content: string) => { },
  },
  gitEndpoint: {
    type: String,
    default: "",
  },
});

const getGitDiff = async () => {
  try {
    const response = await fetch(props.gitEndpoint + "/git-diff");
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    props.contentSetter((await response.json()).diff);
    return;
  } catch (error) {
    console.error("Failed to fetch git diff:", error);
    return null;
  }
};

onMounted(() => {
  getGitDiff();
});
</script>
