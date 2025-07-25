<template>
  <v-row justify="center">
    <v-dialog v-model="draftsDialog" max-width="900px">
      <!-- <template v-slot:activator="{ on, attrs }">
              <v-btn color="primary" theme="dark" v-bind="attrs" v-on="on">Open Dialog</v-btn>
            </template>-->
      <v-card>
        <v-card-title>
          <span class="text-h5 text-primary">{{
            __("Select Sales Orders")
          }}</span>
        </v-card-title>
        <v-card-text class="pa-0">
          <v-container>
            <v-row class="mb-4">
              <v-text-field color="primary" :label="frappe._('Order ID')" bg-color="white" hide-details
                v-model="order_name" density="compact" clearable class="mx-4"></v-text-field>
              <v-btn variant="text" class="ml-2" color="primary" theme="dark" @click="search_orders">{{ __("Search")
                }}</v-btn>
            </v-row>
            <v-row no-gutters>
              <v-col cols="12" class="pa-1">
                <v-data-table :headers="headers" :items="dialog_data" item-key="name" class="elevation-1" show-select
                  v-model="selected" return-object select-strategy="single">
                  <!-- <template v-slot:item.posting_time="{ item }">
                          {{ item.posting_time.split(".")[0] }}
                        </template> -->
                  <template v-slot:item.grand_total="{ item }">
                    {{ currencySymbol(item.currency) }}
                    {{ formatCurrency(item.grand_total) }}
                  </template>
                </v-data-table>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" theme="dark" @click="close_dialog">Close</v-btn>
          <v-btn v-if="selected.length" color="success" theme="dark" @click="submit_dialog">Select</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-row>
</template>

<script>

import format from "../../format";
export default {
  // props: ["draftsDialog"],
  mixins: [format],
  data: () => ({
    draftsDialog: false,
    singleSelect: true,
    pos_profile: {},
    selected: [],
    dialog_data: {},
    order_name: "",
    headers: [
      {
        title: __("Customer"),
        key: "customer_name",
        align: "start",
        sortable: true,
      },
      {
        title: __("Date"),
        align: "start",
        sortable: true,
        key: "transaction_date",
      },
      //   {
      //     title: __("Time"),
      //     align: "start",
      //     sortable: true,
      //     key: "posting_time",
      //   },
      {
        title: __("Order"),
        key: "name",
        align: "start",
        sortable: true,
      },
      {
        title: __("Amount"),
        key: "grand_total",
        align: "end",
        sortable: false,
      },
    ],
  }),
  watch: {},
  methods: {
    close_dialog() {
      this.draftsDialog = false;
    },

    clearSelected() {
      this.selected = [];
    },

    search_orders() {
      const vm = this;
      frappe.call({
        method: "posawesome.posawesome.api.posapp.search_orders",
        args: {
          order_name: vm.order_name,
          company: this.pos_profile.company,
          currency: this.pos_profile.currency,
        },
        async: false,
        callback: function (r) {
          if (r.message) {
            vm.dialog_data = r.message;
          }
        },
      });
    },

    async submit_dialog() {
      if (this.selected.length > 0) {
        var invoice_doc_for_load = {};
        await frappe.call({
          method:
            "posawesome.posawesome.api.posapp.create_sales_invoice_from_order",
          args: {
            sales_order: this.selected[0].name,
          },
          callback: function (r) {
            if (r.message) {
              invoice_doc_for_load = r.message;
            }
          },
        });
        if (invoice_doc_for_load.items) {
          const selectedItems = this.selected[0].items;
          const loadedItems = invoice_doc_for_load.items;

          const loadedItemsMap = {};
          loadedItems.forEach((item) => {
            loadedItemsMap[item.item_code] = item;
          });

          // Iterate through selectedItems and update or discard items
          for (let i = 0; i < selectedItems.length; i++) {
            const selectedItem = selectedItems[i];
            const loadedItem = loadedItemsMap[selectedItem.item_code];

            if (loadedItem) {
              // Update the fields of selected item with loaded item's values
              selectedItem.qty = loadedItem.qty;
              selectedItem.amount = loadedItem.amount;
              selectedItem.uom = loadedItem.uom;
              selectedItem.rate = loadedItem.rate;
              // Update other fields as needed
            } else {
              // If 'item_code' doesn't exist in loadedItems, discard the item
              selectedItems.splice(i, 1);
              i--; // Adjust the index as items are removed
            }
          }
        }
        this.eventBus.emit("load_order", this.selected[0]);
        this.draftsDialog = false;
        frappe.call({
          method: "posawesome.posawesome.api.posapp.delete_sales_invoice",
          args: {
            sales_invoice: invoice_doc_for_load.name,
          },
          callback: function (r) {
            if (r.message) {
              // invoice_doc_for_load = r.message;
            }
          },
        });
      }
    },
  },
  created: function () {
    this.eventBus.on("open_orders", (data) => {
      this.clearSelected();
      this.draftsDialog = true;
      this.dialog_data = data;
      this.order_name = "";
    });
  },
  mounted() {
    this.eventBus.on("register_pos_profile", (data) => {
      this.pos_profile = data.pos_profile;
    });
  },
  beforeUnmount() {
    this.eventBus.off("open_orders");
    this.eventBus.off("register_pos_profile");
  },
};
</script>
