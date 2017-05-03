'use strict';

CloudApp.controller('VDStatusController', 
    /**
     * The controller of VDStatus model
     * @param $rootScope {Object} AngularJS' root scope object
     * @param $scope {Object} AngularJS' scope object
     * @param $i18next {Object} AngularJS' module for handling locale string
     * @param $madal {Object} AngularJS' module for handling modal dialog
     * @param lodash {Object} AngularJS' module for handling infomation load
     * @param ngTableParams {Object} AngularJS' module for handling table
     * @param CommonHttpService {Object} AngularJS's module for handling HTTP requests
     * @param ToastrService {Object} AngularJS's module for handling toast
     * @param CheckboxGroup {Object} AngularJS's module for handling group checkbox
     * @param ngTableHelper {Object} AngularJS's module for handling table pagination
     * @param VDStatus {Object} Resource request object for virtual desktop
     * @param VDStatusWS {Object} Websocket operation object for virtual desktop
     * @return void
     */
    function ($rootScope, $scope, $i18next, $ngBootbox, $modal, lodash, ngTableParams,
              CommonHttpService, ToastrService, CheckboxGroup, ngTableHelper, VDStatus, VDStatusWS) {

      var page_count = 10;

      $scope.status = [];
      var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.status);
      
      $scope.vdstatus_table = new ngTableParams({
        page: 1,
        count: page_count
      },{
        counts: [],
        getData: function ($defer, params) {
          var searchParams = {page: params.page(), page_size: params.count()};
          VDStatus.query(searchParams, function (data) {
            for(var i = 0; i < data.results.length; ++i) {
              data.results[i].online = true;
            }
            $defer.resolve(data.results);
            $scope.status = data.results;
            ngTableHelper.countPages(params, data.count);
            checkboxGroup.syncObjects($scope.status);
          });
        }
      });

      VDStatusWS.onOpen(function() {
        console.log("Websocket connected");
      });

      VDStatusWS.onError(function(e) {
        console.log("Websocket error occured:", e);
      });

      // Handle messages received for websocket connection
      // TODO: Error handling
      VDStatusWS.onMessage(function(msgEvt) {
        console.log(msgEvt);
        var new_user = true,
          data = JSON.parse(msgEvt.data);
        for(var i = 0; i < $scope.status.length; ++i) {
          if($scope.status[i].user != data.user)
            continue;

          // Online status change
          if(!$scope.status[i].online && data.online) {
            var msg = $i18next('vir_desktop.user') + data.user + $i18next('vir_desktop.do_online');
            ToastrService.success(msg);
          } else if($scope.status[i].online && !data.online) {
            var msg = $i18next('vir_desktop.user') + data.user + $i18next('vir_desktop.do_offline');
            ToastrService.success(msg);
          }

          // VM status change
          if($scope.status[i].vm == null && data.vm != null) {
            var msg = $i18next('vir_desktop.user') + data.user + $i18next('vir_desktop.conn_desktop') + data.vm;
            ToastrService.success(msg);
          } else if($scope.status[i].vm != null && data.vm == null) {
            var msg = $i18next('vir_desktop.user') + data.user + $i18next('vir_desktop.disconn_desktop') + $scope.status[i].vm;
            ToastrService.success(msg);
          }
          $scope.status[i] = data

          new_user = false;
          break;
        }

        if($scope.status.length < page_count && new_user) {
          $scope.status.push(msgEvt.data);
          var msg = $i18next('vir_desktop.user') + msgEvt.data.user + $i18next('vir_desktop.do_online');
          ToastrService.success(msg);
        } 
      });

      /**
       * Action button's controller function which will 
       * send a message through websocket connection.
       * @param user {String} user ID
       * @param vm {String} virtual desktop's ID
       * @param action {String} which action, e.g. 'disconnect'
       * @return void
       */
      $scope.takeAction = function(user, vm, action) {
        VDStatusWS.send(JSON.stringify({
          user: user,
          vm: vm,
          action: action
        }));
      };

      /**
       * Action button's controller function which will 
       * open a software install modal dialog.
       * @param userlist {Array} the array of user ID
       * @return void
       */
      $scope.openSoftwareSetupModal = function(userlist) {
        $modal.open({
          templateUrl: 'softwareconf.html',
          backdrop: 'static',
          controller: 'SoftwareController',
          size: 'lg',
          resolve: {
            userlist: function() {
              return userlist;
            },
            action: function() {
              return 'setup';
            }
          }
        }).result.then(function() {
          checkboxGroup.uncheck();
        });
      };

      /**
       * Action button's controller function which will 
       * open a software uninstall modal dialog.
       * @param userlist {Array} the array of user ID
       * @return void
       */
      $scope.openSoftwareRemoveModal = function(userlist) {
        $modal.open({
          templateUrl: 'softwareconf.html',
          backdrop: 'static',
          controller: 'SoftwareController',
          size: 'lg',
          resolve: {
            userlist: function() {
              return userlist;
            },
            action: function() {
              return 'remove';
            }
          }
        }).result.then(function() {
          checkboxGroup.uncheck();
        });
      };
    }
)

/**
 * The controller of modal dialog
 * @param $scope {Object} AngularJS' scope object
 * @param $modalInstance {Object} AngularJS' module for handling modal dialog
 * @param $i18next {Object} AngularJS' module for handling locale string
 * @param $interval {Object} AngularJS' module for handling interval tasks
 * @param CommonHttpService {Object} AngularJS's module for handling HTTP requests
 * @param ToastrService {Object} AngularJS's module for handling toast
 * @param CheckboxGroup {Object} AngularJS's module for handling group checkbox
 * @param userlist {Array} Array of user ID
 * @param action {String} Which action, 'setup' or 'remove'
 * @return void
 */
.controller('SoftwareController', function($scope, $modalInstance, $i18next, $interval,
    CommonHttpService, ToastrService, CheckboxGroup, userlist, action) {
      $scope.userlist = userlist;
      $scope.softwares = [];
      var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.softwares);
      CommonHttpService.get('/api/software/select' + action + '/?addr=' + userlist[0].ip_addr)
          .then(function(data) {
        $scope.loading = false;
        $scope.softwares = data.softwares;                                                                                              
        checkboxGroup.syncObjects($scope.softwares);                                                                                    
        $scope.error_flag = (data.code == 1);   
      });
      $scope.loading = true;

      $scope.is_submitting = false;
      /**
       * Action button's controller function which will 
       * send a HTTP request to execute actions.
       * @return void
       */
      $scope.commit = function() {
        var users = [],
          vms = [],
          ip_addrs = [],
          softwares = [],
          selected = checkboxGroup.checkedObjects();
        for(var i = 0; i < userlist.length; ++i) {
          users.push(userlist[i].user);
          vms.push(userlist[i].vm);
          ip_addrs.push(userlist[i].ip_addr)
        }
        for(var i = 0; i < selected.length; ++i) {
          softwares.push(selected[i].Product_Id);
        }
        var data = {
          users: users,
          vms: vms,
          ip_addrs: ip_addrs,
          softwares: softwares
        };
        CommonHttpService.post('/api/software/' + action + '/', data).then(function(data) {
          if(data.success) {
            ToastrService.success(data.msg, $i18next('success'));
            var trace_status = function (vm, user, pro) {
              CommonHttpService.get('/api/software/actionstatus?vm='+vm).then(function(data) {
                if(data.status == (action+'_ok') || data.status == 'error')
                  $interval.cancel(pro)
                user.action_state = data.status
              })
            }
            for(var i = 0; i < data.ids.length; ++i) {
              (function(x) {
                var pro = $interval(function() {
                  trace_status(data.ids[x], userlist[x], pro)
                }, 2000)
              })(i);
            }
          }
        });
        $modalInstance.close();
      };
      $scope.cancel = $modalInstance.dismiss;
    }
)

/**
 * The factory method for initializing a websocket instance
 * @param $websocket {Object} AngularJS's module for handling websocket
 * @return ws {Object} An instance of AngularJS's websocket module 
 */
.factory('VDStatusWS', function($websocket) {
  // MGR_WS_ADDR is configured at settings.py
  var ws = $websocket(MGR_WS_ADDR);
    
  return ws;
});

