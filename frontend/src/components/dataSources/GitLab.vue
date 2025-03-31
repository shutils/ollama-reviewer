<template>
    <v-text-field
      name="gitlabHost"
      label="GitLab Host"
      id="host"
      v-model="gitlabHost"
      placeholder="https://gitlab.com"
    ></v-text-field>
    <v-text-field
      name="name"
      label="token"
      id="token"
      type="password"
      v-model="token"
    ></v-text-field>
    <v-text-field
      name="projectId"
      label="Project Id"
      id="project-id"
      type="number"
      v-model="projectId"
      :hint="projectName"
      :persistent-hint="Boolean(projectName)"
      @change="getProjectName"
      :disabled="!token"
      :error="branchError"
      :error-messages="branchError ? 'ブランチ名の取得に失敗しました' : ''"
    ></v-text-field>
    <v-autocomplete
      label="branch"
      :items="projectBranches"
      :disabled="!token || !projectId"
      v-model="selectedBranch"
      @update:menu="getFilePathTree"
    ></v-autocomplete>
    <v-autocomplete
      label="filePathTree"
      :items="filePathTree"
      :disabled="!token || !projectId"
      v-model="selectedFilePath"
      @update:model-value="getFileContent"
    ></v-autocomplete>
</template>

<script setup lang="ts">
import { Gitlab } from "@gitbeaker/rest";

const props = defineProps({
  contentSetter: {
    type: Function,
    default: (content: string) => {},
  },
});

const gitlabHost = ref("");
const token = ref("");
const projectId = ref(0);
const projectName = ref("");
const selectedBranch = ref("");
const projectBranches = ref<string[]>([]);
const selectedFilePath = ref("");
const filePathTree = ref<string[]>([]);
// const fileContent = ref("");
const loading = ref(false);
const branchError = ref(false);

const getClient = () => {
  if (!token.value || !gitlabHost) {
    throw Error("Token or host url is undefined");
  }
  return new Gitlab({
    host: gitlabHost.value,
    token: token.value,
  });
};

const getProjectName = async () => {
  const client = getClient();
  client.Projects.show(projectId.value)
    .then((res) => {
      projectName.value = res.name;
      branchError.value = false;
      getFilePathTree();
      getBranches();
    })
    .catch(() => {
      projectName.value = "";
      branchError.value = true;
    });
};

const getBranches = async () => {
  const client = getClient();
  client.Branches.all(projectId.value).then((branches) => {
    projectBranches.value = branches.map((branch) => branch.name);
  });
};

const getFilePathTree = async () => {
  const client = getClient();
  client.Repositories.allRepositoryTrees(projectId.value, {
    recursive: true,
    ref: selectedBranch.value,
  }).then((res) => {
    filePathTree.value = res
      .filter((file) => file.type === "blob")
      .map((file) => file.path);
  });
};

const getFileContent = async (filePath: string | null) => {
  if (!filePath) {
    return;
  }
  loading.value = true;
  const client = getClient();
  client.RepositoryFiles.showRaw(
    projectId.value,
    filePath,
    selectedBranch.value
  ).then((res) => {
    // fileContent.value = res.toString();
    props.contentSetter(res.toString());
    loading.value = false;
  });
};
</script>
