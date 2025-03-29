<template>
  <v-container class="fill-height">
    <v-row>
      <v-col cols="3">
        <v-autocomplete
          label="Data source"
          :items="dataSourceList"
          v-model="dataSource"
        ></v-autocomplete>
        <GitLab v-if="dataSource === 'GitLab'" :content-setter="contentSetter" />
        <GitDiff v-if="dataSource === 'Git diff'" :content-setter="contentSetter" />
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
        <v-btn
          :color="chatting || !ollamaModel ? 'disable' : 'primary'"
          @click="getChatContent"
          :disabled="chatting || !ollamaModel"
          >レビュー</v-btn
        >
        <v-btn
          class="ml-2"
          :color="chatting ? 'primary' : 'disable'"
          @click="abortChat"
          :disabled="!chatting"
          >停止</v-btn
        >
      </v-col>
      <v-col>
        <v-card>
          <v-toolbar density="compact" title="コンテキスト">
            <v-btn @click="editable = !editable">
              <v-icon
                :icon="editable ? 'mdi-pencil' : 'mdi-pencil-off'"
              ></v-icon>
            </v-btn>
          </v-toolbar>
          <v-textarea
            name="fileBlob"
            :readonly="!editable"
            v-model="fileContent"
            :loading="loading"
            style="min-height: 84vh"
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
          :loading="chatLoading"
          style="min-height: 92vh"
        ></v-textarea>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { Ollama } from "ollama";

const dataSourceList = ref(["GitLab", "Git diff"])
const dataSource = ref("")

const fileContent = ref("");
const loading = ref(false);
const ollamaHost = ref("");
const ollamaModel = ref("");
const ollamaModelList = ref<string[]>([]);
const chatContent = ref("");
const chatting = ref(false);
const chatLoading = ref(false);
const defaultSystemPrompt = `あなたはプロのITエンジニアです。
ユーザーからファイルを受け取り、以下の観点でレビューをしてください。
- セキュリティ
- 効率
- リファクタリングの余地
解答は日本語で行ってください。
以下はユーザーのファイルです。`;
const editable = ref(false);
const gitDiffEndpoint = ref("");
const abortingChat = ref(false);

const systemPrompt = ref(defaultSystemPrompt);

const contentSetter = (content: string) => {
  fileContent.value = content;
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
  chatLoading.value = true;
  chatting.value = true;
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
    chatLoading.value = false;
    if (part.done) {
      return;
    }
    if (abortingChat.value) {
      res.abort();
      abortingChat.value = false;
      return;
    }
    chatContent.value += part.message.content;
  }
  chatting.value = false;
};

const abortChat = async () => {
  abortingChat.value = true;
  chatting.value = false;
  chatLoading.value = false;
};

const getGitDiff = async () => {
  try {
    const response = await fetch(gitDiffEndpoint.value);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    fileContent.value = (await response.json()).diff;
    return;
  } catch (error) {
    console.error("Failed to fetch git diff:", error);
    return null;
  }
};
</script>
