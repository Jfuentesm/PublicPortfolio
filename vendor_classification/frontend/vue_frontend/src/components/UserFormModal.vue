<template>
  <TransitionRoot appear :show="show" as="template">
    <Dialog as="div" @close="closeModal" class="relative z-50">
      <!-- Backdrop -->
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/30 backdrop-blur-sm" aria-hidden="true" />
      </TransitionChild>

      <!-- Full-screen container to center the panel -->
      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <!-- Modal Panel -->
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full max-w-lg transform overflow-hidden rounded-lg bg-white p-6 text-left align-middle shadow-xl transition-all">
              <DialogTitle as="h3" class="text-xl font-semibold leading-6 text-gray-800 border-b border-gray-200 pb-4 mb-5">
                {{ isEditing ? 'Edit User' : 'Create New User' }}
              </DialogTitle>

              <!-- Form -->
              <form @submit.prevent="submitForm" class="space-y-5">
                 <!-- Error Message within Modal -->
                 <div v-if="formError" class="p-3 bg-red-100 border border-red-300 text-red-700 rounded-md text-sm flex items-center space-x-2">
                    <ExclamationTriangleIcon class="h-5 w-5 text-red-600 flex-shrink-0"/>
                    <span>{{ formError }}</span>
                 </div>

                 <!-- Username (Readonly on Edit) -->
                 <div>
                   <label for="username" class="block text-sm font-medium text-gray-700 mb-1">Username <span class="text-red-500">*</span></label>
                   <input
                     type="text"
                     v-model="formData.username"
                     id="username"
                     required
                     class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                     :disabled="isEditing"
                     placeholder="e.g., jsmith"
                   >
                    <p v-if="isEditing" class="text-xs text-gray-500 mt-1">Username cannot be changed after creation.</p>
                 </div>

                 <!-- Email -->
                 <div>
                   <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email <span class="text-red-500">*</span></label>
                   <input
                     type="email"
                     v-model="formData.email"
                     id="email"
                     required
                     class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                     placeholder="e.g., j.smith@example.com"
                   >
                 </div>

                 <!-- Full Name -->
                 <div>
                   <label for="full_name" class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                   <input
                     type="text"
                     v-model="formData.full_name"
                     id="full_name"
                     class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                     placeholder="e.g., John Smith"
                    >
                 </div>

                 <!-- Password -->
                  <div>
                   <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
                       Password {{ isEditing ? '(Leave blank to keep unchanged)' : '' }}
                       <span v-if="!isEditing" class="text-red-500">*</span>
                    </label>
                   <input
                     type="password"
                     v-model="formData.password"
                     id="password"
                     :required="!isEditing"
                     minlength="8"
                     class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                     placeholder="Min. 8 characters"
                    >
                    <p v-if="isEditing && formData.password && formData.password.length < 8" class="text-xs text-red-500 mt-1">Password must be at least 8 characters if changing.</p>
                 </div>

                 <!-- Status Toggles -->
                 <div class="flex items-center space-x-8 pt-2">
                    <div class="flex items-center">
                       <Switch
                         :modelValue="Boolean(formData.is_active)" @update:modelValue="formData.is_active = $event"
                         :class="formData.is_active ? 'bg-primary' : 'bg-gray-200'"
                         class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                       >
                         <span class="sr-only">Active Status</span>
                         <span
                           aria-hidden="true"
                           :class="formData.is_active ? 'translate-x-5' : 'translate-x-0'"
                           class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                         />
                       </Switch>
                       <label for="is_active_label" class="ml-3 block text-sm font-medium text-gray-700">Active</label>
                    </div>
                     <div class="flex items-center">
                       <Switch
                         :modelValue="Boolean(formData.is_superuser)" @update:modelValue="formData.is_superuser = $event"
                         :class="formData.is_superuser ? 'bg-indigo-600' : 'bg-gray-200'"
                         class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                       >
                         <span class="sr-only">Admin Status</span>
                         <span
                           aria-hidden="true"
                           :class="formData.is_superuser ? 'translate-x-5' : 'translate-x-0'"
                           class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                         />
                       </Switch>
                       <label for="is_superuser_label" class="ml-3 block text-sm font-medium text-gray-700">Admin</label>
                    </div>
                 </div>

                <!-- Action Buttons -->
                <div class="mt-6 flex justify-end space-x-3 border-t border-gray-200 pt-5">
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                    @click="closeModal"
                    :disabled="isSubmitting"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    class="inline-flex justify-center items-center rounded-md border border-transparent bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-60"
                    :disabled="isSubmitting"
                  >
                     <svg v-if="isSubmitting" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                         <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                         <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                     </svg>
                    {{ isSubmitting ? 'Saving...' : (isEditing ? 'Update User' : 'Create User') }}
                  </button>
                </div>
              </form>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionRoot,
  TransitionChild,
  Switch // Import Switch component
} from '@headlessui/vue';
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'; // Icon for errors
import type { UserResponse, UserCreateData, UserUpdateData } from '@/services/api';

interface Props {
  show: boolean;
  userToEdit: UserResponse | null;
}

const props = defineProps<Props>();
const emit = defineEmits(['close', 'save']);

// --- Form Data ---
interface FormDataState {
    username: string;
    email: string;
    full_name: string | null;
    password?: string;
    is_active: boolean;
    is_superuser: boolean;
}

const defaultFormData: FormDataState = {
    username: '',
    email: '',
    full_name: null,
    password: '',
    is_active: true,
    is_superuser: false,
};

// Helper to initialize or reset form data
const initializeFormData = (user: UserResponse | null): FormDataState => {
    if (user) {
        return {
            username: user.username,
            email: user.email,
            full_name: user.full_name || null,
            password: '', // Always clear password field on open
            is_active: user.is_active ?? true,
            is_superuser: user.is_superuser ?? false,
        };
    } else {
        return { ...defaultFormData };
    }
};

const formData = ref<FormDataState>(initializeFormData(props.userToEdit));
const formError = ref<string | null>(null);
const isSubmitting = ref(false);

const isEditing = computed(() => !!props.userToEdit);

// --- Watcher to populate form when userToEdit prop changes ---
// --- REMOVED immediate: true ---
watch(() => props.userToEdit, (newUser) => {
    console.log("UserFormModal: Watcher triggered for userToEdit:", newUser ? newUser.username : 'null');
    formData.value = initializeFormData(newUser); // Use the helper function to reset/populate
    formError.value = null; // Clear error when user changes
    isSubmitting.value = false; // Reset submitting state
});

// Watcher to reset state when modal is closed (show becomes false)
watch(() => props.show, (newVal, oldVal) => {
    // Only reset when closing (transitioning from true to false)
    if (oldVal === true && newVal === false) {
        console.log("UserFormModal: Watcher triggered for show=false. Resetting form.");
        // Reset form data to default when modal closes
        formData.value = { ...defaultFormData };
        formError.value = null;
        isSubmitting.value = false;
    }
    // Optionally populate when opening if needed, though the userToEdit watcher handles it
    // if (oldVal === false && newVal === true) {
    //    formData.value = initializeFormData(props.userToEdit);
    // }
});


const closeModal = () => {
  if (isSubmitting.value) return; // Prevent closing while submitting
  emit('close');
};

const submitForm = async () => {
    formError.value = null; // Clear previous errors
    isSubmitting.value = true;

    // Basic Frontend Validation
    if (!formData.value.username.trim()) {
        formError.value = "Username is required.";
        isSubmitting.value = false;
        return;
    }
    if (!formData.value.email.trim() || !/\S+@\S+\.\S+/.test(formData.value.email)) {
        formError.value = "A valid email address is required.";
        isSubmitting.value = false;
        return;
    }

    // Prepare data based on create or edit
    let dataToSend: UserCreateData | UserUpdateData;
    if (isEditing.value) {
        const updateData: UserUpdateData = {
            email: formData.value.email,
            full_name: formData.value.full_name?.trim() || null,
            is_active: formData.value.is_active,
            is_superuser: formData.value.is_superuser,
        };
        if (formData.value.password && formData.value.password.length >= 8) {
            updateData.password = formData.value.password;
        } else if (formData.value.password && formData.value.password.length > 0) {
             formError.value = "Password must be at least 8 characters long if changing.";
             isSubmitting.value = false;
             return;
        }
        dataToSend = updateData;
    } else {
        if (!formData.value.password || formData.value.password.length < 8) {
             formError.value = "Password is required and must be at least 8 characters long.";
             isSubmitting.value = false;
             return;
        }
        const createData: UserCreateData = {
            username: formData.value.username.trim(),
            email: formData.value.email.trim(),
            full_name: formData.value.full_name?.trim() || null,
            password: formData.value.password,
            is_active: formData.value.is_active,
            is_superuser: formData.value.is_superuser,
        };
         dataToSend = createData;
    }

    try {
        // Emit the save event - parent handles API call & closing/resetting isSubmitting
        await emit('save', dataToSend);
    } catch (err: any) {
        // If the parent re-throws the error after handling it
        console.error("Error during form submission (caught in modal):", err);
        formError.value = err.message || "Failed to save user.";
        isSubmitting.value = false; // Ensure button is re-enabled on error
    }
    // Do NOT set isSubmitting to false here if emit was successful, parent controls it.
};

</script>

<style scoped>
/* Add custom styles if needed, though Tailwind should cover most */
</style>