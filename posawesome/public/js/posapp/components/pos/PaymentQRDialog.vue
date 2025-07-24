<template>
  <v-dialog v-model="show" max-width="600px">
    <v-card>
      <v-card-title>{{ __('Select QR Payment Method') }}</v-card-title>
      <v-card-text>
        <div class="qr-payment-container">
          <div class="provider-list">
            <v-btn
              v-for="provider in paymentProviders"
              :key="provider.gateway"
              block
              class="mb-2"
              color="primary"
              @click="selectProvider(provider.gateway)"
            >
              {{ provider.name }}
            </v-btn>
          </div>
          <div class="qr-code-display" v-if="selectedQrCode">
            <img :src="selectedQrCode" alt="QR Code" style="max-width: 200px;" />
            <p>{{ __('Scan to pay') }} {{ invoice.grand_total }} {{ __('with') }} {{ selectedProvider }}</p>
          </div>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn color="error" @click="closeDialog">{{ __('Close') }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { call } from 'frappe-ui';

export default {
  name: 'PaymentQRDialog',
  props: {
    invoice: { type: Object, required: true },
    show: { type: Boolean, default: false },
  },
  data() {
    return {
      paymentProviders: [
        { name: 'Khalti', gateway: 'Khalti' },
        { name: 'Fonepay', gateway: 'Fonepay' },
        { name: 'NepalPay', gateway: 'NepalPay' },
      ],
      selectedQrCode: null,
      selectedProvider: null,
      paymentPollInterval: null,
    };
  },
  watch: {
    show(newVal) {
      if (!newVal && this.paymentPollInterval) {
        clearInterval(this.paymentPollInterval);
      }
    },
  },
  methods: {
    async selectProvider(gateway) {
      this.selectedProvider = gateway;
      try {
        const response = await call('qr_payment_pos.api.get_qr_code', {
          gateway,
          amount: this.invoice.grand_total,
          pos_invoice: this.invoice.name,
        });
        if (response.qr_code_url) {
          this.selectedQrCode = response.qr_code_url;
          this.pollPaymentStatus(gateway, response.transaction_id);
        } else {
          frappe.msgprint(__('Failed to generate QR code for ') + gateway);
        }
      } catch (error) {
        frappe.msgprint(__('Error: ') + error.message);
      }
    },
    pollPaymentStatus(gateway, transaction_id) {
      if (this.paymentPollInterval) clearInterval(this.paymentPollInterval);
      this.paymentPollInterval = setInterval(async () => {
        try {
          const response = await call('qr_payment_pos.api.check_payment_status', {
            gateway,
            transaction_id,
          });
          if (response.status === 'completed') {
            clearInterval(this.paymentPollInterval);
            frappe.msgprint(__('Payment received via ') + gateway);
            this.$emit('payment-confirmed', gateway);
            this.closeDialog();
          }
        } catch (error) {
          frappe.log_error('Payment status check failed: ' + error.message);
        }
      }, 5000); // Poll every 5 seconds
    },
    closeDialog() {
      if (this.paymentPollInterval) clearInterval(this.paymentPollInterval);
      this.selectedQrCode = null;
      this.selectedProvider = null;
      this.$emit('update:show', false);
    },
  },
};
</script>

<style scoped>
.qr-payment-container {
  display: flex;
  gap: 20px;
  padding: 20px;
}
.provider-list {
  flex: 1;
}
.qr-code-display {
  flex: 1;
  text-align: center;
}
</style>