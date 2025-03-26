<template>
  <v-container class="fill-height">
    <v-row>
      <v-col cols="3">
        <v-text-field
          name="gitlabHost"
          label="GitLab Host"
          id="host"
          v-model="gitlabHost"
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
        <v-btn color="primary" @click="getChatContent">レビュー</v-btn>
      </v-col>
      <v-col>
        <v-textarea
          label="選択されたファイルが表示されます"
          name="fileBlob"
          readonly
          v-model="fileContent"
          :loading="loading"
          auto-grow
        ></v-textarea>
      </v-col>
      <v-col>
        <v-textarea
          label="チャット内容が表示されます"
          name="chat"
          readonly
          v-model="chatContent"
          auto-grow
        ></v-textarea>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { Gitlab } from "@gitbeaker/rest";
import ollama from "ollama";

const gitlabHost = ref("https://gitlab.com");
const token = ref("");
const projectId = ref(0);
const projectName = ref("");
const selectedBranch = ref("main");
const projectBranches = ref<string[]>([]);
const selectedFilePath = ref("");
const filePathTree = ref<string[]>([]);
const fileContent = ref("");
const loading = ref(false);
const branchError = ref(false);
const chatContent = ref("");

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
    fileContent.value = res.toString();
    loading.value = false;
  });
};

const getChatContent = async () => {
  ollama
    .chat({
      model: "gemma3:4b",
      messages: [
        {
          role: "system",
          content: `あなたはプロのITエンジニアです。
    ユーザーからファイルを受け取り、以下の観点でレビューをしてください。
    - セキュリティ
    - 効率
    - リファクタリングの余地
    解答は日本語で行ってください。
    以下はユーザーのファイルです。
    `,
        },
        { role: "user", content: fileContent.value },
      ],
      stream: false,
    })
    .then((res) => {
      chatContent.value = res.message.content;
    });
};
</script>
