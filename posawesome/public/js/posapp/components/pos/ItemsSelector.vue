<template>
  <div :style="responsiveStyles">
    <v-card :class="['selection mx-auto my-0 py-0 mt-3 dynamic-card', isDarkTheme ? '' : 'bg-grey-lighten-5']"
      :style="{ height: responsiveStyles['--container-height'], maxHeight: responsiveStyles['--container-height'], backgroundColor: isDarkTheme ? '#121212' : '' }">
      <v-progress-linear :active="loading" :indeterminate="loading" absolute location="top"
        color="info"></v-progress-linear>
      <v-overlay :model-value="loading" class="align-center justify-center" absolute>
        <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
      </v-overlay>
      <!-- Add dynamic-padding wrapper like Invoice component -->
      <div class="dynamic-padding">
        <v-row class="items">
          <v-col class="pb-0">
            <v-text-field density="compact" clearable autofocus variant="solo" color="primary"
              :label="frappe._('Search Items')" hint="Search by item code, serial number, batch no or barcode"
              hide-details v-model="debounce_search" 
              @keydown.esc="esc_event"
              @keydown.enter="search_onchange"
              @click:clear="clearSearch" prepend-inner-icon="mdi-magnify" @focus="handleItemSearchFocus"
              ref="debounce_search">
              <!-- Add camera scan button if enabled -->
              <template v-slot:append-inner v-if="pos_profile.posa_enable_camera_scanning">
                <v-btn icon="mdi-camera" size="small" color="primary" variant="text" @click="startCameraScanning"
                  :title="__('Scan with Camera')">
                </v-btn>
              </template>
            </v-text-field>

          </v-col>
          <v-col cols="3" class="pb-0" v-if="pos_profile.posa_input_qty">
            <v-text-field density="compact" variant="solo" color="primary" :label="frappe._('QTY')" hide-details
              v-model="debounce_qty" type="text" @keydown.enter="enter_event" @keydown.esc="esc_event"
              @focus="clearQty"></v-text-field>
          </v-col>
          <v-col cols="2" class="pb-0" v-if="pos_profile.posa_new_line">
            <v-checkbox v-model="new_line" color="accent" value="true" label="NLine" density="default"
              hide-details></v-checkbox>
          </v-col>
          <v-col cols="12" class="pt-0 mt-0">
            <div fluid class="items" v-if="items_view == 'card'">
              <RecycleScroller :items="filtered_items" :item-size="220" key-field="item_code"
                class="overflow-y-auto dynamic-scroll"
                :style="{ maxHeight: 'calc(' + responsiveStyles['--container-height'] + ' - 80px)' }">
                <template #default="{ item }">
                  <v-col xl="2" lg="3" md="6" sm="6" cols="6" min-height="50">
                    <v-card hover="hover" @click="add_item(item)" class="dynamic-item-card">
                      <v-img :src="item.image ||
                        '/assets/posawesome/js/posapp/components/pos/placeholder-image.png'
                        " class="text-white align-end" gradient="to bottom, rgba(0,0,0,0), rgba(0,0,0,0.4)"
                        height="100px">
                        <v-card-text v-text="item.item_name" class="text-caption px-1 pb-0"></v-card-text>
                      </v-img>
                      <v-card-text class="text--primary pa-1">
                        <div class="text-caption text-primary">
                          {{ currencySymbol(pos_profile.currency) || "" }}
                          {{ format_currency(item.rate, pos_profile.currency, ratePrecision(item.rate)) }}
                        </div>
                        <div v-if="pos_profile.posa_allow_multi_currency && selected_currency !== pos_profile.currency"
                          class="text-caption text-success">
                          {{ currencySymbol(selected_currency) || "" }}
                          {{ format_currency(getConvertedRate(item), selected_currency,
                            ratePrecision(getConvertedRate(item))) }}
                        </div>
                        <div class="text-caption golden--text">
                          {{ format_number(item.actual_qty, 4) || 0 }}
                          {{ item.stock_uom || "" }}
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </template>
              </RecycleScroller>
            </div>
            <div v-else>
              <v-data-table-virtual :headers="headers" :items="filtered_items" class="sleek-data-table overflow-y-auto"
                :style="{ maxHeight: 'calc(' + responsiveStyles['--container-height'] + ' - 80px)' }"
                item-key="item_code" @click:row="click_item_row">

                <template v-slot:item.rate="{ item }">
                  <div>
                    <div class="text-primary">{{ currencySymbol(pos_profile.currency) }}
                      {{ format_currency(item.rate, pos_profile.currency, ratePrecision(item.rate)) }}</div>
                    <div v-if="pos_profile.posa_allow_multi_currency && selected_currency !== pos_profile.currency"
                      class="text-success">
                      {{ currencySymbol(selected_currency) }}
                      {{ format_currency(getConvertedRate(item), selected_currency,
                        ratePrecision(getConvertedRate(item))) }}
                    </div>
                  </div>
                </template>
                <template v-slot:item.actual_qty="{ item }">
                  <span class="golden--text">{{ format_number(item.actual_qty, 4) }}</span>
                </template>
              </v-data-table-virtual>
            </div>
          </v-col>
        </v-row>
      </div>
    </v-card>
    <v-card class="cards mb-0 mt-3 dynamic-padding">
      <v-row no-gutters align="center" justify="center" class="dynamic-spacing-sm">
        <v-col cols="12" class="mb-2">
          <v-select :items="items_group" :label="frappe._('Items Group')" density="compact" variant="solo" hide-details
            v-model="item_group"></v-select>
        </v-col>
        <v-col cols="12" class="mb-2" v-if="pos_profile.posa_enable_price_list_dropdown">
          <v-text-field density="compact" variant="solo" color="primary" :label="frappe._('Price List')" hide-details
            :model-value="active_price_list" readonly></v-text-field>
        </v-col>
        <v-col cols="3" class="dynamic-margin-xs">
          <v-btn-toggle v-model="items_view" color="primary" group density="compact" rounded>
            <v-btn size="small" value="list">{{ __("List") }}</v-btn>
            <v-btn size="small" value="card">{{ __("Card") }}</v-btn>
          </v-btn-toggle>
        </v-col>
        <v-col cols="4" class="dynamic-margin-xs">
          <v-btn size="small" block color="primary" variant="text" @click="show_coupons"
            class="action-btn-consistent">{{
              couponsCount }} {{
              __("Coupons")
            }}</v-btn>
        </v-col>
        <v-col cols="5" class="dynamic-margin-xs">
          <v-btn size="small" block color="primary" variant="text" @click="show_offers" class="action-btn-consistent">{{
            offersCount }} {{
              __("Offers") }}
            : {{ appliedOffersCount }}
            {{ __("Applied") }}</v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- Camera Scanner Component -->
    <CameraScanner v-if="pos_profile.posa_enable_camera_scanning" ref="cameraScanner"
      :scan-type="pos_profile.posa_camera_scan_type || 'Both'" @barcode-scanned="onBarcodeScanned" />
  </div>
</template>

<script type="module">

import format from "../../format";
import _ from "lodash";
import CameraScanner from './CameraScanner.vue';


import { RecycleScroller } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
import { saveItemUOMs, getItemUOMs, getLocalStock, isOffline, initializeStockCache, getItemsStorage, setItemsStorage, getLocalStockCache, setLocalStockCache, initPromise, getCachedPriceListItems, savePriceListItems, updateLocalStockCache, isStockCacheReady, getCachedItemDetails, saveItemDetailsCache } from '../../../offline.js';
import { responsiveMixin } from '../../mixins/responsive.js';

export default {
  mixins: [format, responsiveMixin],
  components: {
    CameraScanner,
    RecycleScroller
  },
  data: () => ({
    pos_profile: "",
    flags: {},
    items_view: "list",
    item_group: "ALL",
    loading: false,
    items_group: ["ALL"],
    items: [],
    search: "",
    first_search: "",
    search_backup: "",
    // Limit the displayed items to avoid overly large lists
    itemsPerPage: 50,
    offersCount: 0,
    appliedOffersCount: 0,
    couponsCount: 0,
    appliedCouponsCount: 0,
    customer_price_list: null,
    customer: null,
    new_line: false,
    qty: 1,
    refresh_interval: null,
    currentRequest: null,
    abortController: null,
    itemDetailsRetryCount: 0,
    itemDetailsRetryTimeout: null,
    items_loaded: false,
    selected_currency: "",
    exchange_rate: 1,
    prePopulateInProgress: false,
    itemWorker: null,
    items_request_token: 0,
  }),

  watch: {
    customer: _.debounce(function () {
      if (this.pos_profile.posa_force_reload_items) {
        if (this.pos_profile.posa_smart_reload_mode) {
          // When limit search is enabled there may be no items yet.
          // Fallback to full reload if nothing is loaded
          if (!this.items_loaded || !this.filtered_items.length) {
            this.items_loaded = false;
            this.get_items(true);
          } else {
            // Only refresh prices for visible items when smart reload is enabled
            this.$nextTick(() => this.refreshPricesForVisibleItems());
          }
        } else {
          // Fall back to full reload
          this.items_loaded = false;
          this.get_items(true);
        }
        return;
      }
      // When the customer changes, avoid reloading all items.
      // Simply refresh prices for visible items only
      if (this.items_loaded && this.filtered_items && this.filtered_items.length > 0) {
        this.$nextTick(() => this.refreshPricesForVisibleItems());
      } else {
        this.get_items();
      }
    }, 300),
    customer_price_list: _.debounce(function () {
      if (this.pos_profile.posa_force_reload_items) {
        if (this.pos_profile.posa_smart_reload_mode) {
          // When limit search is enabled there may be no items yet.
          // Fallback to full reload if nothing is loaded
          if (!this.items_loaded || !this.items.length) {
            this.items_loaded = false;
            this.get_items(true);
          } else {
            // Only refresh prices for visible items when smart reload is enabled
            this.$nextTick(() => this.refreshPricesForVisibleItems());
          }
        } else {
          // Fall back to full reload
          this.items_loaded = false;
          this.get_items(true);
        }
        return;
      }
      // Apply cached rates if available for immediate update
      if (this.items_loaded && this.items && this.items.length > 0) {
        const cached = getCachedPriceListItems(this.customer_price_list);
        if (cached && cached.length) {
          const map = {};
          cached.forEach(ci => { map[ci.item_code] = ci; });
          this.items.forEach(it => {
            const ci = map[it.item_code];
            if (ci) {
              it.rate = ci.rate;
              it.price_list_rate = ci.price_list_rate || ci.rate;
            }
          });
          this.eventBus.emit("set_all_items", this.items);
          this.update_items_details(this.items);
          return;
        }
      }
      // No cache found; keep existing items without reloading from server
    }, 300),
    new_line() {
      this.eventBus.emit("set_new_line", this.new_line);
    },
    filtered_items(new_value, old_value) {
      // Update item details if items changed
      if (
        !this.pos_profile.pose_use_limit_search &&
        new_value.length !== old_value.length
      ) {
        this.update_items_details(new_value);
      }
    },
    // Auto-trigger search when limit search is enabled and the query changes
    first_search: _.debounce(function (val) {
      if (this.pos_profile && this.pos_profile.pose_use_limit_search) {
        this.search_onchange(val);
      }
    }, 300),
  },

  methods: {
    refreshPricesForVisibleItems() {
      const vm = this;
      if (!vm.filtered_items || vm.filtered_items.length === 0) return;

      vm.loading = true;

      // Cancel previous request if any
      if (vm.currentRequest) {
        vm.abortController.abort();
        vm.currentRequest = null;
      }

      const itemCodes = vm.filtered_items.map(it => it.item_code);
      const cacheResult = getCachedItemDetails(vm.pos_profile.name, vm.active_price_list, itemCodes);
      const updates = [];

      cacheResult.cached.forEach(det => {
        const item = vm.filtered_items.find(it => it.item_code === det.item_code);
        if (item) {
          const upd = {
            actual_qty: det.actual_qty,
            serial_no_data: det.serial_no_data,
            batch_no_data: det.batch_no_data,
          };
          if (det.item_uoms && det.item_uoms.length > 0) {
            upd.item_uoms = det.item_uoms;
            saveItemUOMs(item.item_code, det.item_uoms);
          }
          if (det.rate !== undefined) {
            upd.rate = det.rate;
            upd.price_list_rate = det.price_list_rate || det.rate;
          }
          updates.push({ item, upd });
        }
      });

      if (cacheResult.missing.length === 0) {
        vm.$nextTick(() => {
          updates.forEach(({ item, upd }) => Object.assign(item, upd));
          updateLocalStockCache(cacheResult.cached);
          vm.loading = false;
        });
        return;
      }

      vm.abortController = new AbortController();
      const itemsToFetch = vm.filtered_items.filter(it => cacheResult.missing.includes(it.item_code));

      frappe.call({
        method: "posawesome.posawesome.api.posapp.get_items_details",
        args: {
          pos_profile: JSON.stringify(vm.pos_profile),
          items_data: JSON.stringify(itemsToFetch),
          price_list: vm.active_price_list,
        },
        freeze: false,
        signal: vm.abortController.signal,
        callback: function (r) {
          if (r.message) {
            r.message.forEach(updItem => {
              const item = vm.filtered_items.find(it => it.item_code === updItem.item_code);
              if (item) {
                const upd = {
                  actual_qty: updItem.actual_qty,
                  serial_no_data: updItem.serial_no_data,
                  batch_no_data: updItem.batch_no_data,
                };
                if (updItem.item_uoms && updItem.item_uoms.length > 0) {
                  upd.item_uoms = updItem.item_uoms;
                  saveItemUOMs(item.item_code, updItem.item_uoms);
                }
                if (updItem.rate !== undefined) {
                  upd.rate = updItem.rate;
                  upd.price_list_rate = updItem.price_list_rate || updItem.rate;
                }
                updates.push({ item, upd });
              }
            });

            vm.$nextTick(() => {
              updates.forEach(({ item, upd }) => Object.assign(item, upd));
              updateLocalStockCache(r.message);
              saveItemDetailsCache(vm.pos_profile.name, vm.active_price_list, r.message);
              vm.loading = false;
            });
          }
        },
        error: function (err) {
          if (err.name !== 'AbortError') {
            console.error("Error fetching item details:", err);
            vm.loading = false;
          }
        }
      });
    },

    show_offers() {
      this.eventBus.emit("show_offers", "true");
    },
    show_coupons() {
      this.eventBus.emit("show_coupons", "true");
    },
    async get_items(force_server = false) {
      await initPromise;
      const request_token = ++this.items_request_token;
      if (!this.pos_profile) {
        console.error("No POS Profile");
        return;
      }

      if (force_server && this.pos_profile.posa_local_storage) {
        localStorage.setItem("items_storage", "");
      }

      const vm = this;
      this.loading = true;

      console.log("trying to load items")
      let search = this.get_search(this.first_search);
      let gr = vm.item_group !== "ALL" ? vm.item_group.toLowerCase() : "";
      let sr = search || "";

      // Skip reload if items already loaded, not forcing, not searching and limit search disabled
      if (
        this.items_loaded &&
        !force_server &&
        !this.first_search &&
        !this.pos_profile.pose_use_limit_search
      ) {
        console.info("Items already loaded, skipping reload");
        if (this.filtered_items && this.filtered_items.length > 0) {
          this.update_items_details(this.filtered_items);
        }
        this.loading = false;
        return;
      }
      console.log("trying to load items2")

      // Attempt to load cached items for the current price list
      if (
        !force_server &&
        !this.pos_profile.pose_use_limit_search
      ) {
        const cached = getCachedPriceListItems(vm.customer_price_list);
        if (cached && cached.length) {
          vm.items = cached;
          vm.items.forEach((it) => {
            if (!it.item_uoms || it.item_uoms.length === 0) {
              const cachedUoms = getItemUOMs(it.item_code);
              if (cachedUoms.length > 0) {
                it.item_uoms = cachedUoms;
              } else if (it.stock_uom) {
                it.item_uoms = [{ uom: it.stock_uom, conversion_factor: 1.0 }];
              }
            }
          });
          this.eventBus.emit("set_all_items", vm.items);
          vm.loading = false;
          vm.items_loaded = true;

          if (vm.items && vm.items.length > 0) {
            vm.prePopulateStockCache(vm.items);
            vm.update_items_details(vm.items);
          }
          return;
        }
      }

      // Load from localStorage when available and not forcing
      if (
        vm.pos_profile.posa_local_storage &&
        getItemsStorage().length &&
        !vm.pos_profile.pose_use_limit_search &&
        !force_server
      ) {
        vm.items = getItemsStorage();
        // Fallback to cached UOMs when loading from storage
        vm.items.forEach((it) => {
          if (!it.item_uoms || it.item_uoms.length === 0) {
            const cached = getItemUOMs(it.item_code);
            if (cached.length > 0) {
              it.item_uoms = cached;
            } else if (it.stock_uom) {
              it.item_uoms = [{ uom: it.stock_uom, conversion_factor: 1.0 }];
            }
          }
        });
        this.eventBus.emit("set_all_items", vm.items);
        vm.loading = false;
        vm.items_loaded = true;

        if (vm.items && vm.items.length > 0) {
          await vm.prePopulateStockCache(vm.items);
          vm.update_items_details(vm.items);
        }
        return;
      }
      console.log("trying to load items3")

      if (this.itemWorker) {

        try {
          const res = await fetch(
            "/api/method/posawesome.posawesome.api.posapp.get_items",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-Frappe-CSRF-Token": frappe.csrf_token,
              },
              credentials: "same-origin",
              body: JSON.stringify({
                pos_profile: JSON.stringify(vm.pos_profile),
                price_list: vm.customer_price_list,
                item_group: gr,
                search_value: sr,
                customer: vm.customer,
              }),
            }
          );



          const text = await res.text();
          // console.log(text)
          this.itemWorker.onmessage = async (ev) => {
            console.log("trying to load items6")
            if (this.items_request_token !== request_token) return;
            if (ev.data.type === "parsed") {
              const parsed = ev.data.items;
              vm.items = parsed.message || parsed;
              savePriceListItems(vm.customer_price_list, vm.items);
              // Ensure UOMs are available for each item
              vm.items.forEach((it) => {
                if (it.item_uoms && it.item_uoms.length > 0) {
                  saveItemUOMs(it.item_code, it.item_uoms);
                } else {
                  const cached = getItemUOMs(it.item_code);
                  if (cached.length > 0) {
                    it.item_uoms = cached;
                  } else if (it.stock_uom) {
                    it.item_uoms = [{ uom: it.stock_uom, conversion_factor: 1.0 }];
                  }
                }
              });
              vm.eventBus.emit("set_all_items", vm.items);
              vm.loading = false;
              vm.items_loaded = true;
              console.info("Items Loaded");

              // Pre-populate stock cache when items are freshly loaded
              vm.prePopulateStockCache(vm.items);

              vm.$nextTick(() => {
                if (vm.search && !vm.pos_profile.pose_use_limit_search) {
                  vm.search_onchange();
                }
              });

              // Always refresh quantities after items are loaded
              if (vm.items && vm.items.length > 0) {
                vm.update_items_details(vm.items);
              }

              if (
                vm.pos_profile.posa_local_storage &&
                !vm.pos_profile.pose_use_limit_search
              ) {
                try {
                  setItemsStorage(vm.items);
                  vm.items.forEach((it) => {
                    if (it.item_uoms && it.item_uoms.length > 0) {
                      saveItemUOMs(it.item_code, it.item_uoms);
                    }
                  });
                } catch (e) {
                  console.error(e);
                }
              }

              if (vm.pos_profile.pose_use_limit_search) {
                vm.enter_event();
              }
            } else if (ev.data.type === "error") {
              console.error('Item worker parse error:', ev.data.error);
              vm.loading = false;
            }
          };
          this.itemWorker.postMessage({ type: 'parse_and_cache', json: text, priceList: vm.customer_price_list });


        } catch (err) {
          console.error('Failed to fetch items', err);
          vm.loading = false;
        }
      } else {
        frappe.call({
          method: "posawesome.posawesome.api.posapp.get_items",
          args: {
            pos_profile: JSON.stringify(vm.pos_profile),
            price_list: vm.customer_price_list,
            item_group: gr,
            search_value: sr,
            customer: vm.customer,
          },
          callback: async function (r) {
            if (vm.items_request_token !== request_token) return;
            if (r.message) {
              vm.items = r.message;
              // Ensure UOMs are available for each item
              vm.items.forEach((it) => {
                if (it.item_uoms && it.item_uoms.length > 0) {
                  saveItemUOMs(it.item_code, it.item_uoms);
                } else {
                  const cached = getItemUOMs(it.item_code);
                  if (cached.length > 0) {
                    it.item_uoms = cached;
                  } else if (it.stock_uom) {
                    it.item_uoms = [{ uom: it.stock_uom, conversion_factor: 1.0 }];
                  }
                }
              });
              vm.eventBus.emit("set_all_items", vm.items);
              vm.loading = false;
              vm.items_loaded = true;
              savePriceListItems(vm.customer_price_list, vm.items);
              console.info("Items Loaded");

              // Pre-populate stock cache when items are freshly loaded
              vm.prePopulateStockCache(vm.items);

              vm.$nextTick(() => {
                if (vm.search && !vm.pos_profile.pose_use_limit_search) {
                  vm.search_onchange();
                }
              });

              // Always refresh quantities after items are loaded
              if (vm.items && vm.items.length > 0) {
                vm.update_items_details(vm.items);
              }

              if (
                vm.pos_profile.posa_local_storage &&
                !vm.pos_profile.pose_use_limit_search
              ) {
                try {
                  setItemsStorage(r.message);
                  r.message.forEach((it) => {
                    if (it.item_uoms && it.item_uoms.length > 0) {
                      saveItemUOMs(it.item_code, it.item_uoms);
                    }
                  });
                } catch (e) {
                  console.error(e);
                }
              }
              if (vm.pos_profile.pose_use_limit_search) {
                vm.enter_event();
              }
            }
          }
        });
      }
    },
    get_items_groups() {
      if (!this.pos_profile) {
        console.log("No POS Profile");
        return;
      }
      if (this.pos_profile.item_groups.length > 0) {
        this.pos_profile.item_groups.forEach((element) => {
          if (element.item_group !== "All Item Groups") {
            this.items_group.push(element.item_group);
          }
        });
      } else {
        const vm = this;
        frappe.call({
          method: "posawesome.posawesome.api.posapp.get_items_groups",
          args: {},
          callback: function (r) {
            if (r.message) {
              r.message.forEach((element) => {
                vm.items_group.push(element.name);
              });
            }
          },
        });
      }
    },
    getItemsHeaders() {
      const items_headers = [
        {
          title: __("Name"),
          align: "start",
          sortable: true,
          key: "item_name",
        },
        {
          title: __("Code"),
          align: "start",
          sortable: true,
          key: "item_code",
        },
        { title: __("Rate"), key: "rate", align: "start" },
        { title: __("Available QTY"), key: "actual_qty", align: "start" },
        { title: __("UOM"), key: "stock_uom", align: "start" },
      ];
      if (!this.pos_profile.posa_display_item_code) {
        items_headers.splice(1, 1);
      }

      return items_headers;
    },
    click_item_row(event, { item }) {
      this.add_item(item)
    },
    add_item(item) {
      item = { ...item };
      if (item.has_variants) {
        this.eventBus.emit("open_variants_model", item, this.items);
      } else {
        if (item.actual_qty === 0 && this.pos_profile.posa_display_items_in_stock) {
          this.eventBus.emit("show_message", {
            title: `No stock available for ${item.item_name}`,
            color: "warning",
          });
          this.update_items_details([item]);
          return;
        }

        // Ensure UOMs are initialized before adding the item
        if (!item.item_uoms || item.item_uoms.length === 0) {
          // If UOMs are not available, fetch them first
          this.update_items_details([item]);

          // Add stock UOM as fallback
          if (!item.item_uoms || item.item_uoms.length === 0) {
            item.item_uoms = [{ uom: item.stock_uom, conversion_factor: 1.0 }];
          }
        }

        // Convert rate if multi-currency is enabled
        if (this.pos_profile.posa_allow_multi_currency &&
          this.selected_currency !== this.pos_profile.currency) {
          // Store original rate as base_rate
          item.base_rate = item.rate;
          item.base_price_list_rate = item.price_list_rate;

          // Set converted rates
          item.rate = this.getConvertedRate(item);
          item.price_list_rate = this.getConvertedRate(item);

          // Set currency
          item.currency = this.selected_currency;
        }

        if (!item.qty || item.qty === 1) {
          const qtyVal = this.qty != null ? this.qty : 1;
          item.qty = Math.abs(qtyVal);
        }
        this.eventBus.emit("add_item", item);
        this.qty = 1;
      }
      this.$forceUpdate();
    },
    enter_event() {
      console.log("Enter Event trigger:", this);
      let match = false;
      if (!this.filtered_items.length || !this.first_search) {
        return;
      }
      const qty = this.get_item_qty(this.first_search);
      const new_item = { ...this.filtered_items[0] };
      new_item.qty = flt(qty);
      new_item.item_barcode.forEach((element) => {
        if (this.search == element.barcode) {
          new_item.uom = element.posa_uom;
          // Call calc_uom to update rate based on new UOM
          this.eventBus.emit("calc_uom", new_item, element.posa_uom);
          match = true;
        }
      });
      if (
        !new_item.to_set_serial_no &&
        new_item.has_serial_no &&
        this.pos_profile.posa_search_serial_no
      ) {
        new_item.serial_no_data.forEach((element) => {
          if (this.search && element.serial_no == this.search) {
            new_item.to_set_serial_no = this.first_search;
            match = true;
          }
        });
      }
      if (this.flags.serial_no) {
        new_item.to_set_serial_no = this.flags.serial_no;
      }
      if (
        !new_item.to_set_batch_no &&
        new_item.has_batch_no &&
        this.pos_profile.posa_search_batch_no
      ) {
        new_item.batch_no_data.forEach((element) => {
          if (this.search && element.batch_no == this.search) {
            new_item.to_set_batch_no = this.first_search;
            new_item.batch_no = this.first_search;
            match = true;
          }
        });
      }
      if (this.flags.batch_no) {
        new_item.to_set_batch_no = this.flags.batch_no;
      }
      const normalizedSearch = this.search?.toLowerCase();
      if (
        normalizedSearch === new_item.item_code?.toLowerCase() ||
        normalizedSearch === new_item.item_name?.toLowerCase()
      ) {
        match = true;
      }
      console.log("Enter Event trigger (match):", match);
      if (match) {
        this.add_item(new_item);
        this.flags.serial_no = null;
        this.flags.batch_no = null;
        this.qty = 1;
        this.debounce_search = ""; // Clear the search input
        this.$refs.debounce_search.focus();
      }

      console.log("Enter Event trigger Last:", new_item);
    },
    search_onchange: _.debounce(function (newSearchTerm) {
      console.log("Search OnChange trigger:", this);
      const vm = this;
      if (newSearchTerm) vm.search = newSearchTerm;
      
      if (vm.pos_profile.pose_use_limit_search) {
        vm.get_items();
      } else {
        // Save the current filtered items before search to maintain quantity data
        const current_items = [...vm.filtered_items];
        if (vm.search && vm.search.length >= 3) {
          vm.enter_event();
        }

        // After search, update quantities for newly filtered items
        if (vm.filtered_items && vm.filtered_items.length > 0) {
          setTimeout(() => {
            vm.update_items_details(vm.filtered_items);
          }, 300);
        }
      }
      console.log("Search OnChange trigger Last:", vm);
    }, 300),
    get_item_qty(first_search) {
      const qtyVal = this.qty != null ? this.qty : 1;
      let scal_qty = Math.abs(qtyVal);
      if (first_search.startsWith(this.pos_profile.posa_scale_barcode_start)) {
        let pesokg1 = first_search.substr(7, 5);
        let pesokg;
        if (pesokg1.startsWith("0000")) {
          pesokg = "0.00" + pesokg1.substr(4);
        } else if (pesokg1.startsWith("000")) {
          pesokg = "0.0" + pesokg1.substr(3);
        } else if (pesokg1.startsWith("00")) {
          pesokg = "0." + pesokg1.substr(2);
        } else if (pesokg1.startsWith("0")) {
          pesokg =
            pesokg1.substr(1, 1) + "." + pesokg1.substr(2, pesokg1.length);
        } else if (!pesokg1.startsWith("0")) {
          pesokg =
            pesokg1.substr(0, 2) + "." + pesokg1.substr(2, pesokg1.length);
        }
        scal_qty = pesokg;
      }
      return scal_qty;
    },
    get_search(first_search) {
      let search_term = "";
      if (
        first_search &&
        first_search.startsWith(this.pos_profile.posa_scale_barcode_start)
      ) {
        search_term = first_search.substr(0, 7);
      } else {
        search_term = first_search;
      }
      return search_term;
    },
    esc_event() {
      this.search = null;
      this.first_search = null;
      this.search_backup = null;
      this.qty = 1;
      this.$refs.debounce_search.focus();
    },
    update_items_details(items) {
      const vm = this;
      if (!items || !items.length) return;

      // reset any pending retry timer
      if (vm.itemDetailsRetryTimeout) {
        clearTimeout(vm.itemDetailsRetryTimeout);
        vm.itemDetailsRetryTimeout = null;
      }

      const itemCodes = items.map(it => it.item_code);
      const cacheResult = getCachedItemDetails(vm.pos_profile.name, vm.active_price_list, itemCodes);
      cacheResult.cached.forEach(det => {
        const item = items.find(it => it.item_code === det.item_code);
        if (item) {
          Object.assign(item, {
            actual_qty: det.actual_qty,
            serial_no_data: det.serial_no_data,
            batch_no_data: det.batch_no_data,
            has_batch_no: det.has_batch_no,
            has_serial_no: det.has_serial_no,
          });
          if (det.item_uoms && det.item_uoms.length > 0) {
            item.item_uoms = det.item_uoms;
            saveItemUOMs(item.item_code, det.item_uoms);
          }
          if (det.rate !== undefined) {
            item.rate = det.rate;
            item.price_list_rate = det.price_list_rate || det.rate;
          }
        }
      });

      let allCached = cacheResult.missing.length === 0;
      items.forEach((item) => {
        const localQty = getLocalStock(item.item_code);
        if (localQty !== null) {
          item.actual_qty = localQty;
        } else {
          allCached = false;
        }

        if (!item.item_uoms || item.item_uoms.length === 0) {
          const cachedUoms = getItemUOMs(item.item_code);
          if (cachedUoms.length > 0) {
            item.item_uoms = cachedUoms;
          } else if (isOffline()) {
            item.item_uoms = [{ uom: item.stock_uom, conversion_factor: 1.0 }];
          } else {
            allCached = false;
          }
        }
      });

      // When offline or everything is cached, skip server call
      if (isOffline() || allCached) {
        vm.itemDetailsRetryCount = 0;
        return;
      }

      // Cancel previous request
      if (vm.currentRequest) {
        vm.abortController.abort();
        vm.currentRequest = null;
      }

      vm.abortController = new AbortController();

      const itemsToFetch = items.filter(it => cacheResult.missing.includes(it.item_code));

      vm.currentRequest = frappe.call({
        method: "posawesome.posawesome.api.posapp.get_items_details",
        args: {
          pos_profile: JSON.stringify(vm.pos_profile),
          items_data: JSON.stringify(itemsToFetch),
          price_list: vm.active_price_list,
        },
        // Avoid freezing the UI while item details are fetched
        freeze: false,
        signal: vm.abortController.signal,
        callback: function (r) {
          if (r.message) {
            vm.itemDetailsRetryCount = 0;
            let qtyChanged = false;
            let updatedItems = [];

            // Batch updates to minimize reactivity triggers
            vm.$nextTick(() => {
              items.forEach((item) => {
                const updated_item = r.message.find(
                  (element) => element.item_code == item.item_code
                );
                if (updated_item) {
                  // Save previous quantity for comparison
                  const prev_qty = item.actual_qty;

                  // Prepare updates but don't apply them yet
                  updatedItems.push({
                    item: item,
                    updates: {
                      actual_qty: updated_item.actual_qty,
                      serial_no_data: updated_item.serial_no_data,
                      batch_no_data: updated_item.batch_no_data,
                      has_batch_no: updated_item.has_batch_no,
                      has_serial_no: updated_item.has_serial_no,
                      item_uoms: updated_item.item_uoms && updated_item.item_uoms.length > 0 ?
                        updated_item.item_uoms : item.item_uoms
                    }
                  });

                  // Track significant quantity changes
                  if (prev_qty > 0 && updated_item.actual_qty === 0) {
                    qtyChanged = true;
                  }

                  // Cache UOMs separately
                  if (updated_item.item_uoms && updated_item.item_uoms.length > 0) {
                    saveItemUOMs(item.item_code, updated_item.item_uoms);
                  }
                }
              });

              // Apply all updates in one batch
              updatedItems.forEach(({ item, updates }) => {
                Object.assign(item, updates);
              });

              // Update local stock cache with latest quantities
              updateLocalStockCache(r.message);
              saveItemDetailsCache(vm.pos_profile.name, vm.active_price_list, r.message);

              // Force update if any item's quantity changed significantly
              if (qtyChanged) {
                vm.$forceUpdate();
              }
            });
          }
        },
        error: function (err) {
          if (err.name !== 'AbortError') {
            console.error("Error fetching item details:", err);
            // Fallback to local stock if server call fails
            items.forEach((item) => {
              const localQty = getLocalStock(item.item_code);
              if (localQty !== null) {
                item.actual_qty = localQty;
              }
              // Fallback to cached UOMs when offline or request fails
              if (!item.item_uoms || item.item_uoms.length === 0) {
                const cached = getItemUOMs(item.item_code);
                if (cached.length > 0) {
                  item.item_uoms = cached;
                }
              }
            });

            // do not retry if offline, wait for "server-online" event instead
            if (!isOffline()) {
              vm.itemDetailsRetryCount += 1;
              const delay = Math.min(32000, 1000 * Math.pow(2, vm.itemDetailsRetryCount - 1));
              vm.itemDetailsRetryTimeout = setTimeout(() => {
                vm.update_items_details(items);
              }, delay);
            }
          }
        }
      });

      // Cleanup on component destroy
      this.cleanupBeforeDestroy = () => {
        if (vm.abortController) {
          vm.abortController.abort();
        }
      };
    },
    update_cur_items_details() {
      if (this.filtered_items && this.filtered_items.length > 0) {
        this.update_items_details(this.filtered_items);
      }
    },
    async prePopulateStockCache(items) {
      if (this.prePopulateInProgress) {
        return;
      }
      this.prePopulateInProgress = true;
      try {
        // Use the new isStockCacheReady function
        if (isStockCacheReady()) {
          console.debug('Stock cache already initialized');
          return;
        }

        console.info('Pre-populating stock cache for', items.length, 'items');
        await initializeStockCache(items, this.pos_profile);
      } catch (error) {
        console.error('Failed to pre-populate stock cache:', error);
      } finally {
        this.prePopulateInProgress = false;
      }
    },
    scan_barcoud() {
      const vm = this;
      try {
        // Check if scanner is already attached to document
        if (document._scannerAttached) {
          return;
        }

        onScan.attachTo(document, {
          suffixKeyCodes: [],
          keyCodeMapper: function (oEvent) {
            oEvent.stopImmediatePropagation();
            return onScan.decodeKeyEvent(oEvent);
          },
          onScan: function (sCode) {
            setTimeout(() => {
              vm.trigger_onscan(sCode);
            }, 300);
          },
        });

        // Mark document as having scanner attached
        document._scannerAttached = true;
      } catch (error) {
        console.warn('Scanner initialization error:', error.message);
      }
    },
//     scan_barcode() {
//       console.log("Scan Barcode event trigger: ", this);
//   const vm = this;

//   try {
//     if (document._scannerAttached) return;

//     onScan.attachTo(document, {
//       suffixKeyCodes: [13], // assumes scanner ends with Enter
//       reactToPaste: true,
//       minLength: 3,
//       avgTimeByChar: 30,
//       onScan(sCode, oEvent) {
//         console.log('Scanned barcode:', sCode);
//         setTimeout(() => {
//           vm.trigger_onscan(sCode);
//         }, 300);
//       },
//       onScanError(oEvent) {
//         console.warn('Scan error:', oEvent);
//       },
//       keyCodeMapper(oEvent) {
//         oEvent.stopImmediatePropagation();
//         return onScan.decodeKeyEvent(oEvent);
//       },
//     });

//     document._scannerAttached = true;
//     console.log('Scanner listener attached');
//   } catch (error) {
//     console.warn('Scanner initialization error:', error.message);
//   }
// },

    trigger_onscan(sCode) {
      if (this.filtered_items.length == 0) {
        this.eventBus.emit("show_message", {
          title: `No Item has this barcode "${sCode}"`,
          color: "error",
        });
        frappe.utils.play_sound("error");
      } else {
        this.enter_event();
      }
    },
    generateWordCombinations(inputString) {
      const words = inputString.split(" ");
      const wordCount = words.length;
      const combinations = [];

      // Helper function to generate all permutations
      function permute(arr, m = []) {
        if (arr.length === 0) {
          combinations.push(m.join(" "));
        } else {
          for (let i = 0; i < arr.length; i++) {
            const current = arr.slice();
            const next = current.splice(i, 1);
            permute(current.slice(), m.concat(next));
          }
        }
      }

      permute(words);

      return combinations;
    },
    clearSearch() {
      this.search_backup = this.first_search;
      this.first_search = "";
      this.search = "";
      // No need to call get_items() again
    },

    restoreSearch() {
      if (this.first_search === "") {
        this.first_search = this.search_backup;
        this.search = this.search_backup;
        // No need to reload items when focus is lost
      }
    },
    handleItemSearchFocus() {
      this.first_search = "";
      this.search = "";
      // Optionally, you might want to also clear search_backup if the behaviour should be a full reset on focus
      // this.search_backup = "";
      //this.debounce_search = '';
      this.focusAndSelectSearch();
    },

    focusAndSelectSearch() {
       this.$nextTick(() => {
        const input = this.$refs.debounce_search?.$el?.querySelector('input');
        if (input) {
          input.select();
        }
      });
    },

    clearQty() {
      this.qty = null;
    },

    startCameraScanning() {
      if (this.$refs.cameraScanner) {
        this.$refs.cameraScanner.startScanning();
      }
    },
    onBarcodeScanned(scannedCode) {
      console.log('Barcode scanned:', scannedCode);

      // Clear any previous search
      this.search = '';
      this.first_search = '';

      // Set the scanned code as search term
      this.first_search = scannedCode;
      this.search = scannedCode;

      // Show scanning feedback
      frappe.show_alert({
        message: `Scanning for: ${scannedCode}`,
        indicator: 'blue'
      }, 2);

      // Enhanced item search and submission logic
      setTimeout(() => {
        this.processScannedItem(scannedCode);
      }, 300);
    },
    processScannedItem(scannedCode) {
      // First try to find exact match by barcode
      let foundItem = this.items.find(item =>
        item.barcode === scannedCode ||
        item.item_code === scannedCode ||
        (item.barcodes && item.barcodes.some(bc => bc.barcode === scannedCode))
      );

      if (foundItem) {
        console.log('Found item by exact match:', foundItem);
        this.addScannedItemToInvoice(foundItem, scannedCode);
        return;
      }

      // If no exact match, try partial search
      const searchResults = this.searchItemsByCode(scannedCode);

      if (searchResults.length === 1) {
        console.log('Found item by search:', searchResults[0]);
        this.addScannedItemToInvoice(searchResults[0], scannedCode);
      } else if (searchResults.length > 1) {
        // Multiple matches - show selection dialog
        this.showMultipleItemsDialog(searchResults, scannedCode);
      } else {
        // No matches found
        this.handleItemNotFound(scannedCode);
      }
    },
    searchItemsByCode(code) {
      return this.items.filter(item => {
        const searchTerm = code.toLowerCase();
        return (
          item.item_code.toLowerCase().includes(searchTerm) ||
          item.item_name.toLowerCase().includes(searchTerm) ||
          (item.barcode && item.barcode.toLowerCase().includes(searchTerm)) ||
          (item.barcodes && item.barcodes.some(bc => bc.barcode.toLowerCase().includes(searchTerm)))
        );
      });
    },
    addScannedItemToInvoice(item, scannedCode) {
      console.log('Adding scanned item to invoice:', item, scannedCode);

      // Use existing add_item method with enhanced feedback
      this.add_item(item);

      // Show success message
      frappe.show_alert({
        message: `Added: ${item.item_name}`,
        indicator: 'green'
      }, 3);

      // Clear search after successful addition
      setTimeout(() => {
        this.clearSearch();
      }, 1000);
    },
    showMultipleItemsDialog(items, scannedCode) {
      // Create a dialog to let user choose from multiple matches
      const dialog = new frappe.ui.Dialog({
        title: __('Multiple Items Found'),
        fields: [
          {
            fieldtype: 'HTML',
            fieldname: 'items_html',
            options: this.generateItemSelectionHTML(items, scannedCode)
          }
        ],
        primary_action_label: __('Cancel'),
        primary_action: () => dialog.hide()
      });

      dialog.show();

      // Add click handlers for item selection
      setTimeout(() => {
        items.forEach((item, index) => {
          const button = dialog.$wrapper.find(`[data-item-index="${index}"]`);
          button.on('click', () => {
            this.addScannedItemToInvoice(item, scannedCode);
            dialog.hide();
          });
        });
      }, 100);
    },
    generateItemSelectionHTML(items, scannedCode) {
      let html = `<div class="mb-3"><strong>Scanned Code:</strong> ${scannedCode}</div>`;
      html += '<div class="item-selection-list">';

      items.forEach((item, index) => {
        html += `
          <div class="item-option p-3 mb-2 border rounded cursor-pointer" data-item-index="${index}" style="border: 1px solid #ddd; cursor: pointer;">
            <div class="d-flex align-items-center">
              <img src="${item.image || '/assets/posawesome/js/posapp/components/pos/placeholder-image.png'}" 
                   style="width: 50px; height: 50px; object-fit: cover; margin-right: 15px;" />
              <div>
                <div class="font-weight-bold">${item.item_name}</div>
                <div class="text-muted small">${item.item_code}</div>
                <div class="text-primary">${this.format_currency(item.rate, this.pos_profile.currency, this.ratePrecision(item.rate))}</div>
              </div>
            </div>
          </div>
        `;
      });

      html += '</div>';
      return html;
    },
    handleItemNotFound(scannedCode) {
      console.warn('Item not found for scanned code:', scannedCode);

      // Show error message
      frappe.show_alert({
        message: `Item not found: ${scannedCode}`,
        indicator: 'red'
      }, 5);

      // Keep the search term for manual search
      this.trigger_onscan(scannedCode);
    },

    getConvertedRate(item) {
      if (!item.rate) return 0;
      if (!this.exchange_rate) return item.rate;

      // If exchange rate is 300 PKR = 1 USD
      // To convert PKR to USD: divide by exchange rate
      // Example: 3000 PKR / 300 = 10 USD
      const convertedRate = item.rate / this.exchange_rate;
      return this.flt(convertedRate, 4);
    },
    currencySymbol(currency) {
      return get_currency_symbol(currency);
    },
    format_currency(value, currency, precision) {
      const prec =
        typeof precision === 'number' ? precision : this.currency_precision;
      return this.formatCurrency(value, prec);
    },
    ratePrecision(value) {
      const numericValue = typeof value === 'string' ? parseFloat(value) : value;
      return Number.isInteger(numericValue) ? 0 : this.currency_precision;
    },
    format_number(value, precision) {
      const prec =
        typeof precision === 'number' ? precision : this.float_precision;
      return this.formatFloat(value, prec);
    },
    hasDecimalPrecision(value) {
      // Check if the value has any decimal precision when multiplied by exchange rate
      if (this.exchange_rate && this.exchange_rate !== 1) {
        let convertedValue = value * this.exchange_rate;
        return !Number.isInteger(convertedValue);
      }
      return !Number.isInteger(value);
    },
  },

  computed: {
    headers() {
      return this.getItemsHeaders();
    },
    filtered_items() {
      this.search = this.get_search(this.first_search);
      if (!this.pos_profile.pose_use_limit_search) {
        let filtred_list = [];
        let filtred_group_list = [];
        if (this.item_group != "ALL") {
          filtred_group_list = this.items.filter((item) =>
            item.item_group
              .toLowerCase()
              .includes(this.item_group.toLowerCase())
          );
        } else {
          filtred_group_list = this.items;
        }
        if (!this.search || this.search.length < 3) {
          let filtered = [];
          if (
            this.pos_profile.posa_show_template_items &&
            this.pos_profile.posa_hide_variants_items
          ) {
            filtered = filtred_group_list
              .filter((item) => !item.variant_of)
              .slice(0, this.itemsPerPage);
          } else {
            filtered = filtred_group_list.slice(0, this.itemsPerPage);
          }

          // Ensure quantities are defined
          filtered.forEach(item => {
            if (item.actual_qty === undefined) {
              item.actual_qty = 0;
            }
          });

          return filtered;
        } else if (this.search) {
          const term = this.search.toLowerCase();
          // Match barcode directly
          filtred_list = filtred_group_list.filter(item =>
            item.item_barcode.some(b => b.barcode === this.search)
          );

          if (filtred_list.length === 0) {
            // Match by code or name containing the term
            filtred_list = filtred_group_list.filter(item =>
              item.item_code.toLowerCase().includes(term) ||
              item.item_name.toLowerCase().includes(term)
            );
          }

          if (filtred_list.length === 0) {
            // Fallback to partial fuzzy match on name
            const search_combinations = this.generateWordCombinations(this.search);
            filtred_list = filtred_group_list.filter(item => {
              const nameLower = item.item_name.toLowerCase();
              return search_combinations.some(element => {
                element = element.toLowerCase().trim();
                const element_regex = new RegExp(`.*${element.split('').join('.*')}.*`);
                return element_regex.test(nameLower);
              });
            });
          }

          if (
            filtred_list.length === 0 &&
            this.pos_profile.posa_search_serial_no
          ) {
            filtred_list = filtred_group_list.filter(item => {
              for (let element of item.serial_no_data) {
                if (element.serial_no === this.search) {
                  this.flags.serial_no = this.search;
                  return true;
                }
              }
              return false;
            });
          }

          if (
            filtred_list.length === 0 &&
            this.pos_profile.posa_search_batch_no
          ) {
            filtred_list = filtred_group_list.filter(item => {
              for (let element of item.batch_no_data) {
                if (element.batch_no === this.search) {
                  this.flags.batch_no = this.search;
                  return true;
                }
              }
              return false;
            });
          }
        }

        let final_filtered_list = [];
        if (
          this.pos_profile.posa_show_template_items &&
          this.pos_profile.posa_hide_variants_items
        ) {
          final_filtered_list = filtred_list.filter((item) => !item.variant_of).slice(0, this.itemsPerPage);
        } else {
          final_filtered_list = filtred_list.slice(0, this.itemsPerPage);
        }

        // Ensure quantities are defined for each item
        final_filtered_list.forEach(item => {
          if (item.actual_qty === undefined) {
            item.actual_qty = 0;
          }
        });

        // Force request quantity update for filtered items
        if (final_filtered_list.length > 0) {
          setTimeout(() => {
            this.update_items_details(final_filtered_list);
          }, 100);
        }

        return final_filtered_list;
      } else {
        const items_list = this.items.slice(0, this.itemsPerPage);

        // Ensure quantities are defined
        items_list.forEach(item => {
          if (item.actual_qty === undefined) {
            item.actual_qty = 0;
          }
        });

        return items_list;
      }
    },
    debounce_search: {
      get() {
        return this.first_search;
      },
      set: _.debounce(function (newValue) {
        this.first_search = newValue;
      }, 200),
    },
    debounce_qty: {
      get() {
        // Display the raw quantity while typing to avoid forced decimal format
        return this.qty === null || this.qty === '' ? '' : this.qty;
      },
      set: _.debounce(function (value) {
        let parsed = parseFloat(String(value).replace(/,/g, ''));
        if (isNaN(parsed)) {
          parsed = null;
        }
        this.qty = parsed;
      }, 200),
    },
    isDarkTheme() {
      return this.$theme.current === 'dark';
    },
    active_price_list() {
      return this.customer_price_list || (this.pos_profile && this.pos_profile.selling_price_list);
    }
  },

  created: function () {
    if (typeof Worker !== 'undefined') {
      try {
        const workerUrl = '/assets/posawesome/js/posapp/workers/itemWorker.js?worker';
        this.itemWorker = new Worker(workerUrl, { type: 'classic' });

        this.itemWorker.onerror = function (event) {
          console.error('Worker error:', event);
          console.error('Message:', event.message);
          console.error('Filename:', event.filename);
          console.error('Line number:', event.lineno);
        };
        console.log("Created worker nowwwwww")
      } catch (e) {
        console.error('Failed to start item worker', e);
        this.itemWorker = null;
      }
    }
    this.$nextTick(function () { });
    this.eventBus.on("register_pos_profile", async (data) => {
      await initPromise;
      this.pos_profile = data.pos_profile;
      if (this.pos_profile.posa_force_reload_items && !this.pos_profile.posa_smart_reload_mode) {
        await this.get_items(true);
      } else {
        await this.get_items();
      }
      this.get_items_groups();
      this.items_view = this.pos_profile.posa_default_card_view
        ? "card"
        : "list";
    });
    this.eventBus.on("update_cur_items_details", () => {
      this.update_cur_items_details();
    });
    this.eventBus.on("update_offers_counters", (data) => {
      this.offersCount = data.offersCount;
      this.appliedOffersCount = data.appliedOffersCount;
    });
    this.eventBus.on("update_coupons_counters", (data) => {
      this.couponsCount = data.couponsCount;
      this.appliedCouponsCount = data.appliedCouponsCount;
    });
    this.eventBus.on("update_customer_price_list", (data) => {
      this.customer_price_list = data;
    });
    this.eventBus.on("update_customer", (data) => {
      this.customer = data;
    });

    // Refresh item quantities when connection to server is restored
    this.eventBus.on("server-online", async () => {
      if (this.items && this.items.length > 0) {
        await this.update_items_details(this.items);
      }
    });

    // Setup auto-refresh for item quantities
    // Trigger an immediate refresh once items are available
    this.update_cur_items_details();
    this.refresh_interval = setInterval(() => {
      if (this.filtered_items && this.filtered_items.length > 0) {
        this.update_cur_items_details();
      }
    }, 30000); // Refresh every 30 seconds after the initial fetch

    // Add new event listener for currency changes
    this.eventBus.on("update_currency", (data) => {
      this.selected_currency = data.currency;
      this.exchange_rate = data.exchange_rate;
    });
  },

  mounted() {
    this.scan_barcoud();
  },

  beforeUnmount() {
    // Clear interval when component is destroyed
    if (this.refresh_interval) {
      clearInterval(this.refresh_interval);
    }

    if (this.itemDetailsRetryTimeout) {
      clearTimeout(this.itemDetailsRetryTimeout);
    }
    this.itemDetailsRetryCount = 0;

    // Call cleanup function for abort controller
    if (this.cleanupBeforeDestroy) {
      this.cleanupBeforeDestroy();
    }

    // Detach scanner if it was attached
    if (document._scannerAttached) {
      try {
        onScan.detachFrom(document);
        document._scannerAttached = false;
      } catch (error) {
        console.warn('Scanner detach error:', error.message);
      }
    }

    if (this.itemWorker) {
      this.itemWorker.terminate();
    }

    this.eventBus.off("update_currency");
    this.eventBus.off("server-online");
  },
};
</script>

<style scoped>
.dynamic-card {
  composes: pos-card;
}

.dynamic-padding {
  padding: var(--dynamic-xs) var(--dynamic-sm) var(--dynamic-xs) var(--dynamic-sm);
}

.dynamic-scroll {
  transition: max-height var(--transition-normal);
}

.dynamic-item-card {
  margin: var(--dynamic-xs);
  transition: var(--transition-normal);
  background-color: var(--surface-secondary);
}

.dynamic-item-card:hover {
  transform: scale(calc(1 + 0.02 * var(--font-scale)));
}

.text-success {
  color: #4CAF50 !important;
}

.sleek-data-table {
  composes: pos-table;
  margin: var(--dynamic-xs);
}

.sleek-data-table:hover {
  box-shadow: var(--shadow-md) !important;
}

/* Light mode card backgrounds */
.selection,
.cards {
  background-color: var(--surface-secondary) !important;
}

/* Consistent spacing with navbar and system */
.dynamic-spacing-sm {
  padding: var(--dynamic-sm) !important;
}

.action-btn-consistent {
  margin-top: var(--dynamic-xs) !important;
  padding: var(--dynamic-xs) var(--dynamic-sm) !important;
  transition: var(--transition-normal) !important;
}

.action-btn-consistent:hover {
  background-color: rgba(25, 118, 210, 0.1) !important;
  transform: translateY(-1px) !important;
}

/* Ensure consistent spacing with navbar pattern */
.cards {
  margin-top: var(--dynamic-sm) !important;
  padding: var(--dynamic-sm) !important;
}

/* Responsive breakpoints */
@media (max-width: 768px) {
  .dynamic-padding {
    padding: var(--dynamic-xs) var(--dynamic-xs) var(--dynamic-xs) var(--dynamic-xs);
  }

  .dynamic-spacing-sm {
    padding: var(--dynamic-xs) !important;
  }

  .action-btn-consistent {
    padding: var(--dynamic-xs) !important;
    font-size: 0.875rem !important;
  }
}

@media (max-width: 480px) {
  .dynamic-padding {
    padding: var(--dynamic-xs) var(--dynamic-xs) var(--dynamic-xs) var(--dynamic-xs);
  }

  .cards {
    padding: var(--dynamic-xs) !important;
  }
}
</style>
