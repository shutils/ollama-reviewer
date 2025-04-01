<template>
  <v-container class="fill-height">
    <v-row>
      <v-col cols="2">
        <v-autocomplete
          label="Data source"
          :items="dataSourceList"
          v-model="dataSource"
        ></v-autocomplete>
        <GitLab
          v-if="dataSource === 'GitLab'"
          :content-setter="contentSetter"
        />
        <GitSource
          v-if="dataSource === 'Git Agent'"
          :content-setter="contentSetter"
        />
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
        <div class="d-flex">
          <v-autocomplete
            label="プロンプトリスト"
            :items="systemPromptOptions.map(option => option.title)"
            v-model="selectedSystemPromptTitle"
            @update:modelValue="updateSystemPrompt"
          ></v-autocomplete>
          <v-btn
            @click="showPromptEditor = true"
            class="mt-1 ml-2"
            icon="mdi-cog"
          ></v-btn>
        </div>
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
      <v-col cols="5">
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
      <v-col cols="5">
        <v-card
          class="overflow-y-scroll overflow-x-scroll"
          height="90vh"
          :loading="chatLoading"
        >
          <div v-html="parcedChatContent" class="pa-2"></div>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="showPromptEditor">
      <v-card>
        <v-card-title>システムプロンプトの編集</v-card-title>
        <v-card-text>
          <v-data-table
            :items="systemPromptOptions"
            item-value="title"
            class="elevation-1"
            dense
            editable
          >
            <template v-slot:top>
              <v-toolbar flat>
                <v-toolbar-title>プロンプトリスト</v-toolbar-title>
                <v-spacer></v-spacer>
                <v-btn @click="addPrompt" color="primary" small>追加</v-btn>
              </v-toolbar>
            </template>
            <template v-slot:body="{ items }">
              <tr v-for="(item, index) in items" :key="index">
                <td>
                  <v-text-field
                    v-model="item.title"
                    label="タイトル"
                    dense
                  ></v-text-field>
                </td>
                <td>
                  <v-textarea
                    v-model="item.content"
                    label="内容"
                    dense
                    auto-grow
                  ></v-textarea>
                </td>
                <td>
                  <v-btn
                    icon
                    @click="removePrompt(index)"
                    color="red"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </td>
              </tr>
            </template>
          </v-data-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showPromptEditor = false" color="primary">閉じる</v-btn>
          <v-btn
            @click="exportPrompts"
            color="primary"
          >エクスポート</v-btn>
          <v-btn
            @click="importPrompts"
            color="primary"
          >インポート</v-btn>
          <input
            type="file"
            ref="fileInput"
            accept=".json"
            style="display: none"
            @change="handleFileImport"
          />
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { Ollama } from "ollama/browser";
import { Marked } from "marked";
import { markedHighlight } from "marked-highlight";
import hljs from "highlight.js";
import "highlight.js/styles/github-dark.css";
import GitSource from "@/components/dataSources/GitAgent/Main.vue";

const marked = new Marked(
  markedHighlight({
    emptyLangClass: "hljs",
    langPrefix: "hljs language-",
    highlight(code, lang, info) {
      const language = hljs.getLanguage(lang) ? lang : "plaintext";
      return hljs.highlight(code, { language }).value;
    },
  })
);

const dataSourceList = ref(["GitLab", "Git Agent"]);
const dataSource = ref("");

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
const abortingChat = ref(false);
const parcedChatContent = ref("");

const systemPrompt = ref(defaultSystemPrompt);

const systemPromptOptions = ref([
  {
    title: "ITエンジニアのレビュー",
    content: `あなたはプロのITエンジニアです。ユーザーからファイルを受け取り、以下の観点でレビューをしてください。\n- セキュリティ\n- 効率\n- リファクタリングの余地\n解答は日本語で行ってください。\n以下はユーザーのファイルです。`
  },
  {
    title: "コード品質のレビュー",
    content: `あなたはコード品質の専門家です。以下のコードをレビューし、改善点を提案してください。\n- 可読性\n- 保守性\n- パフォーマンス\n解答は日本語で行ってください。`
  },
  {
    title: "セキュリティリスクの指摘",
    content: `あなたはセキュリティエンジニアです。以下のコードをレビューし、潜在的なセキュリティリスクを指摘してください。\n解答は日本語で行ってください。`
  }
]);

const selectedSystemPromptTitle = ref("");

const updateSystemPrompt = () => {
  const selectedOption = systemPromptOptions.value.find(
    option => option.title === selectedSystemPromptTitle.value
  );
  if (selectedOption) {
    systemPrompt.value = selectedOption.content;
  }
};

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
      break;
    }
    if (abortingChat.value) {
      res.abort();
      abortingChat.value = false;
      break;
    }
    chatContent.value += part.message.content;
    parcedChatContent.value = await marked.parse(chatContent.value);
  }
  chatting.value = false;
  appendCopyButton()
};

const abortChat = async () => {
  abortingChat.value = true;
  chatting.value = false;
  chatLoading.value = false;
};

const appendCopyButton = () => {
  document.querySelectorAll("pre").forEach((pre) => {
    const code = pre.querySelector("code.hljs") as HTMLElement;
    if (!code) return;
    if (code.querySelector("button.copy-button")) {
      return
    }

    const copyButton = document.createElement("button");
    copyButton.textContent = "コピー";
    copyButton.classList.add("copy-button");

    copyButton.addEventListener("click", () => {
      navigator.clipboard.writeText(code.innerText).then(() => {
        copyButton.textContent = "コピーしました!";
        setTimeout(() => (copyButton.textContent = "コピー"), 2000);
      });
    });

    pre.style.position = "relative";
    pre.prepend(copyButton);
  });
};

const showPromptEditor = ref(false);

const LOCAL_STORAGE_KEY = "systemPromptOptions";

const loadPromptsFromLocalStorage = () => {
  const savedPrompts = localStorage.getItem(LOCAL_STORAGE_KEY);
  if (savedPrompts) {
    systemPromptOptions.value = JSON.parse(savedPrompts);
  }
};

const savePromptsToLocalStorage = () => {
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(systemPromptOptions.value));
};

const addPrompt = () => {
  systemPromptOptions.value.push({ title: "", content: "" });
  savePromptsToLocalStorage();
};

const removePrompt = (index: number) => {
  systemPromptOptions.value.splice(index, 1);
  savePromptsToLocalStorage();
};

const fileInput = ref<HTMLInputElement | null>(null);

const exportPrompts = () => {
  const dataStr = JSON.stringify(systemPromptOptions.value, null, 2);
  const blob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "prompts.json";
  a.click();
  URL.revokeObjectURL(url);
};

const importPrompts = () => {
  fileInput.value?.click();
};

const handleFileImport = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedPrompts = JSON.parse(e.target?.result as string);
        if (Array.isArray(importedPrompts)) {
          systemPromptOptions.value = importedPrompts;
          savePromptsToLocalStorage();
        } else {
          alert("無効なファイル形式です。");
        }
      } catch {
        alert("ファイルの読み込み中にエラーが発生しました。");
      }
    };
    reader.readAsText(file);
  }
};

watch(systemPromptOptions, savePromptsToLocalStorage, { deep: true });

onMounted(() => {
  loadPromptsFromLocalStorage();
  appendCopyButton();
});
</script>

<style>
.copy-button {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  border-radius: 5px;
}

.copy-button:hover {
  background: rgba(0, 0, 0, 0.9);
}
</style>
