/**
 * PBL系统路由配置
 */

// PBL学生端路由
const studentRoutes = {
  path: '/pbl/student',
  component: () => import('@/layouts/PBLStudentLayout.vue'),
  meta: { requiresAuth: true, roles: ['student'] },
  redirect: '/pbl/student/courses',
  children: [
    {
      path: 'courses',
      name: 'StudentCourses',
      component: () => import('@pbl/student/views/MyCourses.vue'),
      meta: { title: '我的课程' }
    },
    {
      path: 'courses/:uuid',
      name: 'StudentCourseDetail',
      component: () => import('@pbl/student/views/CourseDetail.vue'),
      meta: { title: '课程详情' }
    },
    {
      path: 'units/:uuid',
      name: 'StudentUnitLearning',
      component: () => import('@pbl/student/views/UnitLearning.vue'),
      meta: { 
        title: '单元学习',
        hideSidebar: true  // 隐藏侧边栏，全屏显示
      }
    },
    {
      path: 'tasks',
      name: 'StudentTasks',
      component: () => import('@pbl/student/views/MyTasks.vue'),
      meta: { title: '我的任务' }
    },
    {
      path: 'projects',
      name: 'StudentProjects',
      component: () => import('@pbl/student/views/MyCourses.vue'),
      meta: { title: '我的项目' }
    },
    {
      path: 'portfolio',
      name: 'StudentPortfolio',
      component: () => import('@pbl/student/views/StudentPortfolio.vue'),
      meta: { title: '我的作品集' }
    },
    {
      path: 'learning-assistant',
      name: 'StudentLearningAssistant',
      component: () => import('@pbl/student/views/LearningAssistant.vue'),
      meta: { 
        title: 'AI学习助手',
        hideSidebar: false  // 显示侧边栏导航
      }
    }
  ]
}

// PBL学校管理平台路由（学校管理员和教师）
// 注意：教师路由已合并到此处，统一管理
const schoolRoutes = {
  path: '/pbl/school',
  component: () => import('@/layouts/PBLSchoolLayout.vue'),
  meta: { requiresAuth: true, roles: ['school_admin', 'teacher'] },
  redirect: '/pbl/school/dashboard',
  children: [
    {
      path: 'dashboard',
      name: 'SchoolDashboard',
      component: () => import('@pbl/school/views/SchoolDashboard.vue'),
      meta: { 
        title: '概览',
        roles: ['school_admin', 'teacher']
      }
    },
    // 教师专用功能
    {
      path: 'my-courses',
      name: 'SchoolMyCourses',
      component: () => import('@pbl/teacher/views/TeacherCourses.vue'),
      meta: { 
        title: '我的课程',
        roles: ['teacher']
      }
    },
    {
      path: 'grading',
      name: 'SchoolGrading',
      component: () => import('@pbl/teacher/views/TeacherTasks.vue'),
      meta: { 
        title: '作业批改',
        roles: ['teacher']
      }
    },
    {
      path: 'my-students',
      name: 'SchoolMyStudents',
      component: () => import('@pbl/teacher/views/TeacherStudents.vue'),
      meta: { 
        title: '我的学生',
        roles: ['teacher']
      }
    },
    // 学校管理员专用功能 - 用户管理
    {
      path: 'users',
      name: 'SchoolUserManagement',
      component: () => import('@pbl/school/views/SchoolUserManagement.vue'),
      meta: { 
        title: '用户管理',
        roles: ['school_admin']
      }
    },
    // 项目式课程管理（班级管理）
    {
      path: 'classes',
      name: 'SchoolClasses',
      component: () => import('@pbl/school/views/ClubClasses.vue'),
      meta: { 
        title: '项目式课程管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'classes/:uuid',
      name: 'SchoolClassDetail',
      component: () => import('@pbl/school/views/ClassDetail.vue'),
      meta: {
        title: '班级详情',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'classes/:uuid/edit',
      name: 'SchoolClassEdit',
      component: () => import('@pbl/admin/views/AdminClassEdit.vue'),
      meta: {
        title: '编辑班级',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'classes/:uuid/members',
      name: 'SchoolClassMembers',
      component: () => import('@pbl/admin/views/AdminClassMembers.vue'),
      meta: {
        title: '成员管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'classes/:uuid/groups',
      name: 'SchoolClassGroups',
      component: () => import('@pbl/admin/views/AdminClassGroups.vue'),
      meta: {
        title: '分组管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'classes/:uuid/teachers',
      name: 'SchoolClassTeachers',
      component: () => import('@pbl/admin/views/AdminClassTeachers.vue'),
      meta: {
        title: '教师管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/courses',
      name: 'SchoolClassCourses',
      component: () => import('@pbl/admin/views/AdminClassCourses.vue'),
      meta: {
        title: '课程管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'classes/:uuid/progress',
      name: 'SchoolClassProgress',
      component: () => import('@pbl/admin/views/AdminClassProgress.vue'),
      meta: {
        title: '学习进度',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'classes/:uuid/progress/units/:unitId',
      name: 'SchoolClassUnitDetail',
      component: () => import('@pbl/admin/views/AdminClassUnitDetail.vue'),
      meta: {
        title: '单元详情',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'classes/:uuid/homework',
      name: 'SchoolClassHomework',
      component: () => import('@pbl/admin/views/AdminClassHomework.vue'),
      meta: {
        title: '作业管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'classes/:uuid/homework/units/:unitId',
      name: 'SchoolClassHomeworkUnitDetail',
      component: () => import('@pbl/admin/views/AdminClassUnitHomework.vue'),
      meta: {
        title: '单元作业',
        roles: ['school_admin', 'teacher']
      }
    },
    // 课程模板库
    {
      path: 'available-templates',
      name: 'SchoolAvailableTemplates',
      component: () => import('@pbl/school/views/AvailableTemplates.vue'),
      meta: { 
        title: '课程模板库',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'template-detail/:uuid',
      name: 'SchoolTemplateDetail',
      component: () => import('@pbl/school/views/TemplateDetail.vue'),
      meta: {
        title: '模板详情',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'statistics',
      name: 'SchoolStatistics',
      component: () => import('@pbl/school/views/SchoolDashboard.vue'),
      meta: { 
        title: '数据统计',
        roles: ['school_admin']
      }
    },
    {
      path: 'learning-assistant',
      name: 'SchoolLearningAssistant',
      component: () => import('@pbl/school/views/LearningAssistantTeacher.vue'),
      meta: { 
        title: 'AI学习助手',
        roles: ['school_admin']
      }
    }
  ]
}

// PBL系统管理平台路由（仅平台管理员）
const adminRoutes = {
  path: '/pbl/admin',
  component: () => import('@pbl/admin/views/AdminDashboard.vue'),
  meta: { requiresAuth: true, roles: ['platform_admin', 'channel_manager'] },
  redirect: '/pbl/admin/schools',
  children: [
    // 平台管理员专用路由
    {
      path: 'schools',
      name: 'AdminSchools',
      component: () => import('@pbl/admin/views/AdminSchools.vue'),
      meta: { 
        title: '学校管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'course-templates',
      name: 'CourseTemplates',
      component: () => import('@pbl/admin/views/CourseTemplates.vue'),
      meta: { 
        title: '课程模板管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'course-templates/:uuid',
      name: 'CourseTemplateDetail',
      component: () => import('@pbl/admin/views/CourseTemplateDetail.vue'),
      meta: { 
        title: '课程模板详情',
        roles: ['platform_admin']
      }
    },
    {
      path: 'template-permissions',
      name: 'TemplatePermissions',
      component: () => import('@pbl/admin/views/TemplatePermissions.vue'),
      meta: { 
        title: '模板授权管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'courses',
      name: 'AdminCourses',
      component: () => import('@pbl/admin/views/AdminCourses.vue'),
      meta: { 
        title: '课程管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'courses/:uuid',
      name: 'AdminCourseDetail',
      component: () => import('@pbl/admin/views/AdminCourseDetail.vue'),
      meta: { 
        title: '课程详情',
        roles: ['platform_admin']
      }
    },
    {
      path: 'units',
      name: 'AdminUnits',
      component: () => import('@pbl/admin/views/AdminUnits.vue'),
      meta: { 
        title: '学习单元',
        roles: ['platform_admin']
      }
    },
    {
      path: 'resources',
      name: 'AdminResources',
      component: () => import('@pbl/admin/views/AdminResources.vue'),
      meta: { 
        title: '资料管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'tasks',
      name: 'AdminTasks',
      component: () => import('@pbl/admin/views/AdminTasks.vue'),
      meta: { 
        title: '任务管理',
        roles: ['platform_admin']
      }
    },
    // 渠道管理功能（平台管理员和渠道管理员共享）
    {
      path: 'channel/partners',
      name: 'AdminChannelPartners',
      component: () => import('@pbl/channel-mgmt/views/ChannelPartners.vue'),
      meta: { 
        title: '渠道商管理',
        roles: ['platform_admin', 'channel_manager']
      }
    },
    {
      path: 'channel/partners/:partnerId',
      name: 'AdminChannelPartnerDetail',
      component: () => import('@pbl/channel-mgmt/views/ChannelPartnerDetail.vue'),
      meta: { 
        title: '渠道商详情',
        roles: ['platform_admin', 'channel_manager']
      }
    },
    {
      path: 'channel/school-assignment',
      name: 'AdminSchoolAssignment',
      component: () => import('@pbl/channel-mgmt/views/AssignSchools.vue'),
      meta: { 
        title: '学校分配',
        roles: ['platform_admin', 'channel_manager']
      }
    },
    {
      path: 'channel/statistics',
      name: 'AdminChannelStatistics',
      component: () => import('@pbl/channel-mgmt/views/ChannelStatistics.vue'),
      meta: { 
        title: '渠道统计',
        roles: ['platform_admin', 'channel_manager']
      }
    }
  ]
}

// PBL渠道商端路由
const channelRoutes = {
  path: '/pbl/channel',
  component: () => import('@/layouts/PBLChannelLayout.vue'),
  meta: { requiresAuth: true, roles: ['channel_partner'] },
  redirect: '/pbl/channel/schools',
  children: [
    {
      path: 'schools',
      name: 'ChannelSchools',
      component: () => import('@pbl/channel/views/ChannelSchools.vue'),
      meta: { title: '合作学校' }
    },
    {
      path: 'schools/:schoolId/courses',
      name: 'ChannelSchoolCourses',
      component: () => import('@pbl/channel/views/ChannelSchoolCourses.vue'),
      meta: { title: '学校课程' }
    },
    {
      path: 'courses/:courseUuid',
      name: 'ChannelCourseDetail',
      component: () => import('@pbl/channel/views/ChannelCourseDetail.vue'),
      meta: { title: '课程详情' }
    }
  ]
}

export default [studentRoutes, schoolRoutes, adminRoutes, channelRoutes]
