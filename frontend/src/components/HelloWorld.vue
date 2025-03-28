<template>
  <v-container class="fill-height">
    <v-row>
      <v-col cols="3">
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
        <v-text-field
          name="gitDiffEndpoint"
          label="Git diff Endpoint"
          id="git-diff-endpoint"
          v-model="gitDiffEndpoint"
          @change="getGitDiff"
        ></v-text-field>
        <v-text-field
          name="ollamaHost"
          label="Ollama Host"
          id="ollama-host"
          v-model="ollamaHost"
          placeholder="http://localhost:11434"
          @change="getOllamaModelList"
        ></v-text-field>
        <v-autocomplete
          label="ollamaModel"
          :items="ollamaModelList"
          :disabled="!(ollamaModelList.length !== 0)"
          v-model="ollamaModel"
        ></v-autocomplete>
        <v-textarea
          label="システムプロンプト"
          name="systemPrompt"
          v-model="systemPrompt"
          auto-grow
        ></v-textarea>
        <v-btn :color="(chatting || !ollamaModel) ? 'disable' : 'primary'" @click="getChatContent" :disabled="chatting || !ollamaModel">レビュー</v-btn>
      </v-col>
      <v-col>
        <v-card>
          <v-toolbar density="compact" title="コンテキスト">
            <v-btn @click="editable = !editable">
              <v-icon :icon="editable ? 'mdi-pencil' : 'mdi-pencil-off'"></v-icon>
            </v-btn>
          </v-toolbar>
          <v-textarea
            name="fileBlob"
            :readonly="!editable"
            v-model="fileContent"
            :loading="loading"
            auto-grow
          >
        </v-textarea>
        </v-card>
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
import { Ollama } from "ollama";

const gitlabHost = ref("");
const token = ref("");
const projectId = ref(0);
const projectName = ref("");
const selectedBranch = ref("");
const projectBranches = ref<string[]>([]);
const selectedFilePath = ref("");
const filePathTree = ref<string[]>([]);
const fileContent = ref("");
const loading = ref(false);
const branchError = ref(false);
const ollamaHost = ref("");
const ollamaModel = ref("");
const ollamaModelList = ref<string[]>([]);
const chatContent = ref("");
const chatting = ref(false);
const defaultSystemPrompt = `あなたはプロのITエンジニアです。
ユーザーからファイルを受け取り、以下の観点でレビューをしてください。
- セキュリティ
- 効率
- リファクタリングの余地
解答は日本語で行ってください。
以下はユーザーのファイルです。`;
const editable = ref(false);
const gitDiffEndpoint = ref("")

const systemPrompt = ref(defaultSystemPrompt);

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

const getOllamaModelList = async () => {
  ollamaModelList.value = [];
  ollamaModel.value = "";
  if (!ollamaHost.value) {
    return;
  }
  const ollamaClient = new Ollama({
    host: ollamaHost.value,
  });
  ollamaClient.list().then((res) => {
    ollamaModelList.value = res.models.map((model) => model.name);
  });
};

const getChatContent = async () => {
  if (!ollamaHost.value) {
    return;
  }
  const ollamaClient = new Ollama({
    host: ollamaHost.value,
  });
  chatContent.value = "";
  const res = await ollamaClient.chat({
    model: ollamaModel.value,
    messages: [
      {
        role: "system",
        content: systemPrompt.value,
      },
      { role: "user", content: fileContent.value },
    ],
    stream: true,
  });
  for await (const part of res) {
    if (part.done) {
      return;
    }
    chatContent.value += part.message.content;
  }
};

const getGitDiff = async () => {
  try {
    const response = await fetch(gitDiffEndpoint.value);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    fileContent.value = (await response.json()).diff;
    return
  } catch (error) {
    console.error("Failed to fetch git diff:", error);
    return null;
  }
}

</script>
