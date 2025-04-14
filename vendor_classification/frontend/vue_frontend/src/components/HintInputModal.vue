<template>
  <TransitionRoot as="template" :show="open">
    <Dialog as="div" class="relative z-10" @close="closeModal">
      <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0" enter-to="opacity-100" leave="ease-in duration-200" leave-from="opacity-100" leave-to="opacity-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" enter-to="opacity-100 translate-y-0 sm:scale-100" leave="ease-in duration-200" leave-from="opacity-100 translate-y-0 sm:scale-100" leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95">
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
              <div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                <div class="sm:flex sm:items-start">
                  <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                    <PencilSquareIcon class="h-6 w-6 text-blue-600" aria-hidden="true" />
                  </div>
                  <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                    <DialogTitle as="h3" class="text-base font-semibold leading-6 text-gray-900">Provide Reclassification Hint</DialogTitle>
                    <div class="mt-2">
                      <p class="text-sm text-gray-600 mb-1">For Vendor: <strong class="font-medium">{{ vendorName }}</strong></p>
                      <p class="text-sm text-gray-500">
                        Please provide a concise hint to help the system re-classify this vendor accurately. Examples: "supplier of laboratory chemicals", "provides marketing consulting services", "industrial fastener manufacturer".
                      </p>
                      <div class="mt-4">
                        <label for="hint" class="sr-only">Hint</label>
                        <textarea
                          id="hint"
                          name="hint"
                          rows="3"
                          v-model="localHint"
                          class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm sm:leading-6"
                          placeholder="Enter hint here..."
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                <button
                  type="button"
                  class="inline-flex w-full justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary sm:ml-3 sm:w-auto disabled:opacity-50"
                  @click="saveHint"
                  :disabled="!localHint || localHint.trim() === ''"
                >
                  Save Hint
                </button>
                <button
                  type="button"
                  class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                  @click="closeModal"
                  ref="cancelButtonRef"
                >
                  Cancel
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { ref, watch, type PropType } from 'vue'
import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue'
import { PencilSquareIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  open: {
    type: Boolean,
    required: true,
  },
  vendorName: {
    type: String,
    required: true,
  },
  initialHint: {
    type: String as PropType<string | null>,
    default: null,
  },
})

const emit = defineEmits(['close', 'save'])

const localHint = ref(props.initialHint || '');

watch(() => props.initialHint, (newVal) => {
  localHint.value = newVal || '';
});

watch(() => props.open, (newVal) => {
  if (newVal) {
    // Reset local hint when modal opens, based on potentially updated prop
    localHint.value = props.initialHint || '';
  }
});


const closeModal = () => {
  emit('close');
}

const saveHint = () => {
  if (localHint.value && localHint.value.trim() !== '') {
    emit('save', localHint.value.trim());
    closeModal();
  }
}
</script>