/**
 * User: arthur 
 * Date: 16-4-17
 **/
CloudApp.controller('InitcloudController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox, $sce, $http, $location,
             CommonHttpService, ToastrService, ngTableParams, ngTableHelper,
             Ceilometer, CheckboxGroup, DataCenter){

        $scope.$on('$viewContentLoaded', function(){
                Metronic.initAjax();
        });
        
        $scope.dashboard = "http://" + $location.host() + ":5601/app/kibana#/dashboard/initcloud_log?_g=(refreshInterval:(display:Off,pause:!f,value:0),time:(from:now-12h,mode:relative,to:now))&_a=(filters:!(),options:(darkTheme:!t),panels:!((col:5,id:LOG_LINE,panelIndex:1,row:1,size_x:7,size_y:8,type:visualization),(col:1,id:LOG_LEVEL,panelIndex:3,row:1,size_x:4,size_y:4,type:visualization),(col:1,id:%E6%9C%8D%E5%8A%A1%E5%8D%A0%E6%AF%94,panelIndex:4,row:5,size_x:4,size_y:4,type:visualization)),query:(query_string:(analyze_wildcard:!t,query:'*')),title:initcloud_log,uiState:())"
        var loadMonitor = function(){
                $scope.monitorUrl = $sce.trustAsResourceUrl($scope.dashboard);
            };
        loadMonitor();
        $scope.ceilometers = [];
        var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.ceilometers);

        $scope.ceilometer_table = new ngTableParams({
                page: 1,
                count: 10
            },{
                counts: [],
                getData: function($defer, params){
                    Ceilometer.query(function(data){
                        $scope.ceilometers = ngTableHelper.paginate(data, $defer, params);
                        checkboxGroup.syncObjects($scope.ceilometers);
                    });
                }
            });



        var deleteCeilometers = function(ids){

            $ngBootbox.confirm($i18next("ceilometer.confirm_delete")).then(function(){

                if(typeof ids == 'function'){
                    ids = ids();
                }

                CommonHttpService.post("/api/ceilometer/batch-delete/", {ids: ids}).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        $scope.ceilometer_table.reload();
                        checkboxGroup.uncheck()
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            });
        };

        $scope.batchDelete = function(){

            deleteCeilometers(function(){
                var ids = [];

                checkboxGroup.forEachChecked(function(Ceilometer){
                    if(ceilometer.checked){
                        ids.push(ceilometer.id);
                    }
                });

                return ids;
            });
        };

        $scope.delete = function(ceilometer){
            deleteCeilometers([ceilometer.id]);
        };


        $scope.edit = function(ceilometer){

            $modal.open({
                templateUrl: 'update.html',
                controller: 'CeilometerUpdateController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    ceilometer_table: function () {
                        return $scope.ceilometer_table;
                    },
                    ceilometer: function(){return ceilometer}
                }
            });
        };

        $scope.openNewCeilometerModal = function(){
            $modal.open({
                templateUrl: 'new-ceilometer.html',
                backdrop: "static",
                controller: 'NewCeilometerController',
                size: 'lg',
                resolve: {
                    dataCenters: function(){
                        return DataCenter.query().$promise;
                    }
                }
            }).result.then(function(){
                $scope.ceilometer_table.reload();
            });
        };
    })


    .controller('NewCeilometerController',
        function($scope, $modalInstance, $i18next,
                 CommonHttpService, ToastrService, CeilometerForm, dataCenters){

            var form = null;
            $modalInstance.rendered.then(function(){
                form = CeilometerForm.init($scope.site_config.WORKFLOW_ENABLED);
            });

            $scope.dataCenters = dataCenters;
            $scope.ceilometer = {is_resource_user: false, is_approver: false};
            $scope.is_submitting = false;
            $scope.cancel = $modalInstance.dismiss;
            $scope.create = function(){

                if(form.valid() == false){
                    return;
                }

                $scope.is_submitting = true;
                CommonHttpService.post('/api/ceilometer/create/', $scope.ceilometer).then(function(result){
                    if(result.success){
                        ToastrService.success(result.msg, $i18next("success"));
                        $modalInstance.close();
                    } else {
                        ToastrService.error(result.msg, $i18next("op_failed"));
                    }
                    $scope.is_submitting = true;
                }).finally(function(){
                    $scope.is_submitting = false;
                });
            };
        }

   ).factory('CeilometerForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            ceilometername: {
                                required: true,
                                remote: {
                                    url: "/api/ceilometer/is-name-unique/",
                                    data: {
                                        ceilometername: $("#ceilometername").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            ceilometername: {
                                remote: $i18next('ceilometer.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#ceilometerForm', config);
                }
            }
        }]).controller('CeilometerUpdateController',
        function($rootScope, $scope, $modalInstance, $i18next,
                 ceilometer, ceilometer_table,
                 Ceilometer, UserDataCenter, ceilometerForm,
                 CommonHttpService, ToastrService, ResourceTool){

            $scope.ceilometer = ceilometer = angular.copy(ceilometer);

            $modalInstance.rendered.then(ceilometerForm.init);

            $scope.cancel = function () {
                $modalInstance.dismiss();
            };


            var form = null;
            $modalInstance.rendered.then(function(){
                form = ceilometerForm.init($scope.site_config.WORKFLOW_ENABLED);
            });
            $scope.submit = function(ceilometer){

                if(!$("#CeilometerForm").validate().form()){
                    return;
                }

                ceilometer = ResourceTool.copy_only_data(ceilometer);


                CommonHttpService.post("/api/ceilometer/update/", ceilometer).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        ceilometer_table.reload();
                        $modalInstance.dismiss();
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            };
        }
   ).factory('ceilometerForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            ceilometername: {
                                required: true,
                                remote: {
                                    url: "/api/ceilometer/is-name-unique/",
                                    data: {
                                        ceilometername: $("#ceilometername").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            ceilometername: {
                                remote: $i18next('ceilometer.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#CeilometerForm', config);
                }
            }
        }]);
