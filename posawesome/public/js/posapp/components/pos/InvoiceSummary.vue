<template>
  <v-card
    :class="['cards mb-0 mt-3 py-2 px-3 rounded-lg', isDarkTheme ? '' : 'bg-grey-lighten-4']"
    :style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
  >
    <v-row dense>
      <!-- Summary Info -->
      <v-col cols="12" md="7">
        <v-row dense>
          <!-- Total Qty -->
          <v-col cols="6">
            <v-text-field :model-value="formatFloat(total_qty)" :label="frappe._('Total Qty')"
              prepend-inner-icon="mdi-format-list-numbered" variant="solo" density="compact" readonly
              color="accent" />
          </v-col>
          <!-- Additional Discount (Amount or Percentage) -->
          <v-col cols="6" v-if="!pos_profile.posa_use_percentage_discount">
            <v-text-field :model-value="additional_discount" @update:model-value="$emit('update:additional_discount', $event)"
              :label="frappe._('Additional Discount')" prepend-inner-icon="mdi-cash-minus" variant="solo"
              density="compact" color="warning" :prefix="currencySymbol(pos_profile.currency)"
              :disabled="!pos_profile.posa_allow_user_to_edit_additional_discount" />
          </v-col>

          <v-col cols="6" v-else>
            <v-text-field :model-value="additional_discount_percentage" @update:model-value="$emit('update:additional_discount_percentage', $event)" @change="$emit('update_discount_umount')"
              :rules="[isNumber]" :label="frappe._('Additional Discount %')" suffix="%"
              prepend-inner-icon="mdi-percent" variant="solo" density="compact" color="warning"
              :disabled="!pos_profile.posa_allow_user_to_edit_additional_discount || !!discount_percentage_offer_name" />
          </v-col>

          <!-- Items Discount -->
          <v-col cols="6">
            <v-text-field :model-value="formatCurrency(total_items_discount_amount)"
              :prefix="currencySymbol(displayCurrency)" :label="frappe._('Items Discounts')"
              prepend-inner-icon="mdi-tag-minus" variant="solo" density="compact" color="warning" readonly />
          </v-col>

          <!-- Total (moved to maintain row alignment) -->
          <v-col cols="6">
            <v-text-field :model-value="formatCurrency(subtotal)" :prefix="currencySymbol(displayCurrency)"
              :label="frappe._('Total')" prepend-inner-icon="mdi-cash" variant="solo" density="compact" readonly
              color="success" />
          </v-col>
        </v-row>
      </v-col>

      <!-- Action Buttons -->
      <v-col cols="12" md="5">
        <v-row dense>
          <v-col cols="6">
            <v-btn
              block
              color="accent"
              theme="dark"
              prepend-icon="mdi-content-save"
              @click="$emit('save-and-clear')"
            >
              {{ __('Save & Clear') }}
            </v-btn>
          </v-col>
          <v-col cols="6">
            <v-btn
              block
              color="warning"
              theme="dark"
              prepend-icon="mdi-file-document"
              @click="$emit('load-drafts')"
              class="white-text-btn"
            >
              {{ __('Load Drafts') }}
            </v-btn>
          </v-col>
          <v-col cols="6" v-if="pos_profile.custom_allow_select_sales_order == 1">
            <v-btn
              block
              color="info"
              theme="dark"
              prepend-icon="mdi-book-search"
              @click="$emit('select-order')"
            >
              {{ __('Select S.O') }}
            </v-btn>
          </v-col>
          <v-col cols="6">
            <v-btn
              block
              color="error"
              theme="dark"
              prepend-icon="mdi-close-circle"
              @click="$emit('cancel-sale')"
            >
              {{ __('Cancel Sale') }}
            </v-btn>
          </v-col>
          <v-col cols="6" v-if="pos_profile.posa_allow_return == 1">
            <v-btn
              block
              color="secondary"
              theme="dark"
              prepend-icon="mdi-backup-restore"
              @click="$emit('open-returns')"
            >
              {{ __('Sales Return') }}
            </v-btn>
          </v-col>
          <!-- <v-col cols="6" v-if="pos_profile.posa_allow_print_draft_invoices">
            <v-btn
              block
              color="primary"
              theme="dark"
              prepend-icon="mdi-printer"
              @click="$emit('print-draft')"
            >
              {{ __('Print Draft') }}
            </v-btn>
          </v-col> -->
          <v-col cols="12">
            <v-btn
              block
              color="success"
              theme="dark"
              size="large"
              prepend-icon="mdi-credit-card"
              @click="$emit('show-payment')"
            >
              {{ __('PAY') }}
            </v-btn>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-card>
</template>

<script>
export default {
  props: {
    pos_profile: Object,
    total_qty: [Number, String],
    additional_discount: Number,
    additional_discount_percentage: Number,
    total_items_discount_amount: Number,
    subtotal: Number,
    displayCurrency: String,
    formatFloat: Function,
    formatCurrency: Function,
    currencySymbol: Function,
    discount_percentage_offer_name: [String, Number],
    isNumber: Function
  },
  emits: [
    'update:additional_discount',
    'update:additional_discount_percentage',
    'update_discount_umount',
    'save-and-clear',
    'load-drafts',
    'select-order',
    'cancel-sale',
    'open-returns',
    'print-draft',
    'show-payment'
  ],
  computed: {
    isDarkTheme() {
      return this.$theme?.current === 'dark';
    }
  }
}
</script>

<style scoped>
.cards {
  background-color: #f5f5f5 !important;
}

:deep(.dark-theme) .cards,
:deep(.dark-theme) .cards .v-card__underlay,
:deep(.v-theme--dark) .cards,
:deep(.v-theme--dark) .cards .v-card__underlay,
:deep(.cards.v-theme--dark),
:deep(.cards.v-theme--dark) .v-card__underlay,
::v-deep(.dark-theme) .cards,
::v-deep(.dark-theme) .cards .v-card__underlay,
::v-deep(.v-theme--dark) .cards,
::v-deep(.v-theme--dark) .cards .v-card__underlay,
::v-deep(.cards.v-theme--dark),
::v-deep(.cards.v-theme--dark) .v-card__underlay {
  background-color: #1E1E1E !important;
}

.white-text-btn {
  color: white !important;
}

.white-text-btn :deep(.v-btn__content) {
  color: white !important;
}
</style>
