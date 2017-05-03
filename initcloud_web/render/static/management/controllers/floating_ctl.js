'use strict';

angular.module("CloudApp")
    .controller('FloatingController',
        function ($rootScope, $scope, $filter, $timeout,
            $interval, $modal, $i18next, ngTableParams, FloatingState,
            CommonHttpService, ToastrService, ngTableHelper, PriceRule) {

            $scope.$on('$viewContentLoaded', function () {
                Metronic.initAjax();
            });

            $scope.current_floating_data = [];
            $scope.selected_floatingIP = false;

            // Get floating data table 
            $scope.floating_table = new ngTableParams({
                page: 1,
                count: 10
            }, {
                counts: [],
                getData: function ($defer, params) {
                    CommonHttpService.get("/api/floatings/").then(function (data) {
                        $scope.current_floating_data = ngTableHelper.paginate(data, $defer, params);
                        FloatingState.processList($scope.current_floating_data);
                    });
                }
            });

           // floating action refresh
            var previous_refresh = false;

            $rootScope.setInterval(function () {

                var list = $scope.current_floating_data;
                var need_refresh = false;
                for (var i = 0; i < list.length; i++) {
                    if (list[i].isUnstable) {
                        need_refresh = true;
                        break;
                    }
                }
                if (need_refresh) {
                    $scope.floating_table.reload();
                    previous_refresh = true;
                } else {
                    if (previous_refresh) {
                        $scope.floating_table.reload();
                    }
                    previous_refresh = false;
                }

            }, 5000);

            // Create floating ip
            $scope.modal_create_floating = function () {
                $modal.open({
                    templateUrl: 'addFloating.html',
                    controller: 'FloatCreateController',
                    backdrop: "static",
                    //size: 'lg',
                    resolve: {
                        floating_table: function () {
                            return $scope.floating_table;
                        },
                        // Get quota
                        quota: function(CommonHttpService){
                            return CommonHttpService.get("/api/account/quota/");
                        },
                        // Get floating prices
                        floatingPrices: function(){
                            return PriceRule.query({'resource_type': 'floating_ip'}).$promise;
                        },
                        bandwidthPrices: function(){
                            return PriceRule.query({'resource_type': 'bandwidth'}).$promise;
                        }
                    }
                });
            };

            // Bind fip to instance
            $scope.modal_binding_instance = function (floating) {
                $modal.open({
                    templateUrl: 'associate.html',
                    controller: 'AssociateController',
                    backdrop: "static",
                    resolve: {
                        floating: function () {
                            return floating;
                        },
                        instances: function () {
                            return CommonHttpService.get("/api/floatings/target_list/");
                        },
                        floating_table: function () {
                            return $scope.floating_table;
                        }
                    }
                });
            };

            // Modal change bandwidth
            $scope.modal_change_bandwidth = function (floating) {
                $scope.floatingIP = floating;
                $modal.open({
                    templateUrl: 'changeBandwidth.html',
                    controller: 'changeBandwidthController',
                    backdrop: "static",
                    size: 'lg',
                    scope: $scope,
                    resolve: {
                        floating_table: function () {
                            return $scope.floating_table;
                        }
                    }
                });

            };

            //Actually action perfrom
            var post_action = function (floating, action) {
                bootbox.confirm($i18next("floatingIP.confirm_" + action), function (confirm) {
                    if (confirm) {
                        var post_data = {
                            "floating_id": floating.id,
                            "action": action
                        };

                        CommonHttpService.post("/api/floatings/action/", post_data).then(function (data) {
                            if (data.OPERATION_STATUS == 1) {
                                ToastrService.success($i18next("op_success_msg"), $i18next("success"));
                                $scope.floating_table.reload();
                            }
                            else {
                                ToastrService.error($i18next("op_failed_msg"), $i18next("op_failed"));
                            }
                        });
                    }
                });
            };

            // Release the fip
            var action_release = function (floating) {
                post_action(floating, "release");
            };
            // Disassociate fip
            var action_disassociate = function (floating) {
                post_action(floating, "disassociate");
            };

            // Total actions
            $scope.floating_action = function (floating, action) {
                var action_func = {
                    "release": action_release,
                    "disassociate": action_disassociate
                };

                action_func[action](floating);
            };
        }
    )

     // Floating create action
    .controller('FloatCreateController',
        function ($rootScope, $scope, $modalInstance, $i18next, lodash,$interval,
                  CommonHttpService, ToastrService, PriceTool,
                  floating_table, quota, floatingPrices, bandwidthPrices) {

            $scope.floatingIP = {"size": 5, "pay_type": "hour", "pay_num": 1};
            $scope.quota = quota;
            $scope.cancel =  $modalInstance.dismiss;

            $scope.isQuotaExhausted = (quota.floating_ip != 0) && quota.floating_ip_used >= quota.floating_ip;

            $scope.usageRatio =  ((quota.floating_ip_used + 1)* 100 / quota.floating_ip) + "%" ;

            $scope.create = function (floating) {
                var params = {"bandwidth": floating.size, "pay_type": "hour", "pay_num": 1};

                CommonHttpService.post("/api/floatings/create/", params).then(function (data) {
                    if (data.OPERATION_STATUS == 1) {
                        ToastrService.success(data.msg, $i18next("success"));
                        floating_table.reload();
                        $modalInstance.close();
                        var floating_id = data.fip

            var trace_status = function (floating_id, pro) {
              CommonHttpService.get('/api/floatings/actionstatus?fip='+floating_id).then(function(data) {
                if(data.status == 0){
                  ToastrService.success(data.msg, $i18next('faied'));
                  $interval.cancel(pro)
                 }
              })
            }
            for(var i = 0; i < 1; ++i) {
              (function(x) {
                var pro = $interval(function() {
                  trace_status(floating_id, pro)
                }, 2000)
              })(i);
            }
                    } else {
                        ToastrService.error($i18next("op_failed_msg"), $i18next("op_failed"));
                    }
                });
            };

            $scope.calculateCost = function(config){
                var floatingPrice = PriceTool.getPrice(floatingPrices, 1, config.pay_type),
                    bandwidthPrice = PriceTool.getPrice(bandwidthPrices, config.size, config.pay_type);

                return floatingPrice + bandwidthPrice;
            };
        }
    )

    // Associate Controller Taking care of exactly action
    .controller('AssociateController',
        function ($rootScope, $scope, $filter, $modalInstance,
                  $i18next, ToastrService, CommonHttpService,
                  floating_table, floating, instances) {

            $scope.cancelBinding = $modalInstance.dismiss;
            $scope.floating = floating;
            $scope.instances = instances;
            $scope.selected_instance = null;
            $scope.has_error = false;

            $scope.associate = function () {
                if (!$scope.selected_instance) {
                    $scope.has_error = true;
                    return;
                }

                var post_data = {
                    "action": "associate",
                    "floating_id": $scope.floating.id,
                    "resource": $scope.selected_instance.id,
                    "resource_type":$scope.selected_instance.resource_type
                };

                CommonHttpService.post("/api/floatings/action/", post_data).then(function (data) {
                    if (data.OPERATION_STATUS == 1) {
                        ToastrService.success($i18next("floatingIP.op_success_and_waiting"), $i18next("success"));
                        floating_table.reload();
                        $modalInstance.close();
                    } else {
                        ToastrService.error($i18next("op_failed_msg"), $i18next("op_failed"));
                    }
                });
            };
        }
    )

    //Slider of bandwidth
    .directive("floatslider", function(){
        return {
            restrict: 'E',
            templateUrl: 'slider.html',
            scope: {
                data: "=data"
            },
            link: function (scope, el, attrs, ctrl) {
                $(el).find("#slider-range-max").slider({
                    isRTL: false,
                    range: "max",
                    min: 1,
                    step: 1,
                    max: 30,
                    value: 5,
                    slide: function (event, ui) {
                        scope.data.size = ui.value;
                        scope.$apply();
                    }
                });
            }
        };
    });
