<template>
  <v-text-field
    name="gitEndpoint"
    label="Git Agent Endpoint"
    id="git-endpoint"
    v-model="gitEndpoint"
  ></v-text-field>
  <v-autocomplete
    label="methodType"
    :items="methods"
    :disabled="!gitEndpoint"
    v-model="method"
  ></v-autocomplete>
  <Diff v-if="method === 'diff'" :content-setter="props.contentSetter" :git-endpoint="gitEndpoint"/>
  <File v-if="method === 'file'" :content-setter="props.contentSetter" :git-endpoint="gitEndpoint"/>
</template>

<script setup lang="ts">
const props = defineProps({
  contentSetter: {
    type: Function,
    default: (content: string) => {},
  },
});

const gitEndpoint = ref("");
const methods = ["diff", "file"] as const;
type Method = (typeof methods)[number];
const method: Ref<Method> = ref("diff");

</script>
