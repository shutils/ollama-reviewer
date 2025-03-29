<template>
  <v-text-field
    name="gitDiffEndpoint"
    label="Git diff Endpoint"
    id="git-diff-endpoint"
    v-model="gitDiffEndpoint"
    @change="getGitDiff"
  ></v-text-field>
</template>

<script setup lang="ts">
const props = defineProps({
  contentSetter: {
    type: Function,
    default: (content: string) => {},
  },
});

const gitDiffEndpoint = ref("");

const getGitDiff = async () => {
  try {
    const response = await fetch(gitDiffEndpoint.value);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    props.contentSetter((await response.json()).diff)
    return;
  } catch (error) {
    console.error("Failed to fetch git diff:", error);
    return null;
  }
};
</script>
