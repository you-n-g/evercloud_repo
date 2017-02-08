/**
 * User: arthur 
 * Date: 16-4-17
 **/
CloudApp.controller('CeilometerController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox, $sce, $http,
             CommonHttpService, ToastrService, ngTableParams, ngTableHelper,
             Ceilometer, CheckboxGroup, DataCenter){

        $scope.$on('$viewContentLoaded', function(){
                Metronic.initAjax();
        });
        $scope.base_url = "http://192.168.1.51:5601/app/kibana#/visualize/";        
        //$scope.monitorUrl = $sce.trustAsResourceUrl("/api/ceilometer_monitor");
        $scope.dashboard = "http://192.168.1.48:5601/app/kibana#/visualize/edit/UDP?_g=(refreshInterval:(display:Off,pause:!f,value:0),time:(from:now-1h,mode:quick,to:now))&_a=(filters:!(),linked:!f,query:(query_string:(analyze_wildcard:!t,query:'*')),uiState:(),vis:(aggs:!((enabled:!t,id:'1',params:(field:counter_volume),schema:metric,type:max),(enabled:!t,id:'2',params:(field:counter_name.keyword,order:desc,orderBy:'1',row:!t,size:5),schema:split,type:terms),(enabled:!t,id:'3',params:(field:resource_id.keyword,order:desc,orderBy:'1',size:5),schema:group,type:terms),(enabled:!t,id:'4',params:(customInterval:'2h',extended_bounds:(),field:'@timestamp',interval:auto,min_doc_count:1),schema:segment,type:date_histogram)),listeners:(),params:(addLegend:!t,addTimeMarker:!f,addTooltip:!t,defaultYExtents:!f,drawLinesBetweenPoints:!t,interpolate:linear,legendPosition:right,radiusRatio:9,scale:linear,setYExtents:!f,shareYAxis:!t,showCircles:!t,smoothLines:!f,times:!(),yAxis:()),title:UDP,type:line))"
        var loadMonitor = function(){
                $scope.monitorUrl = $sce.trustAsResourceUrl($scope.dashboard);
            };
        loadMonitor();
        $scope.changeMeter = function(meter){
                CommonHttpService.post("/api/ceilometer/", {"meter":meter}).then(function (data) {
                $scope.dashboard = data['url'];
                loadMonitor();})
        };
 
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
