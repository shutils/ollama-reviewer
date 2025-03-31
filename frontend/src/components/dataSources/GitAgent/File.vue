<template>
  <v-autocomplete
    label="gitFiles"
    :items="gitFiles"
    :disabled="!(gitFiles.length !== 0)"
    v-model="gitFilePath"
    @update:model-value="getGitFileContent"
  ></v-autocomplete>
</template>

<script setup lang="ts">
const props = defineProps({
  contentSetter: {
    type: Function,
    default: (content: string) => {},
  },
  gitEndpoint: {
    type: String,
    default: "",
  },
});

const gitFiles = ref<string[]>([]);
const gitFilePath = ref("");

const getGitFiles = async () => {
  try {
    const response = await fetch(props.gitEndpoint + "/git-file-ls");
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    gitFiles.value = (await response.json()).files;
    return;
  } catch (error) {
    console.error("Failed to fetch git diff:", error);
    return null;
  }
};

const getGitFileContent = async () => {
  try {
    const response = await fetch(
      props.gitEndpoint + "/git-show" + "?" + "file_path=" + gitFilePath.value
    );
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    props.contentSetter((await response.json()).file_content);
    return;
  } catch (error) {
    console.error("Failed to fetch git diff:", error);
    return null;
  }
};

onMounted(() => {
  getGitFiles();
});
</script>
