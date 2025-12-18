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
    }
  ]
}

// PBL教师端路由
const teacherRoutes = {
  path: '/pbl/teacher',
  component: () => import('@/layouts/PBLTeacherLayout.vue'),
  meta: { requiresAuth: true, roles: ['teacher'] },
  redirect: '/pbl/teacher/dashboard',
  children: [
    {
      path: 'dashboard',
      name: 'TeacherDashboard',
      component: () => import('@pbl/teacher/views/TeacherDashboard.vue'),
      meta: { title: '教学仪表盘' }
    },
    {
      path: 'courses',
      name: 'TeacherCourses',
      component: () => import('@pbl/teacher/views/TeacherCourses.vue'),
      meta: { title: '课程管理' }
    },
    {
      path: 'tasks',
      name: 'TeacherTasks',
      component: () => import('@pbl/teacher/views/TeacherTasks.vue'),
      meta: { title: '任务管理' }
    },
    {
      path: 'students',
      name: 'TeacherStudents',
      component: () => import('@pbl/teacher/views/TeacherStudents.vue'),
      meta: { title: '学生管理' }
    }
  ]
}

// PBL管理端路由
const adminRoutes = {
  path: '/pbl/admin',
  component: () => import('@pbl/admin/views/AdminDashboard.vue'),
  meta: { requiresAuth: true, roles: ['platform_admin', 'school_admin', 'teacher'] },
  redirect: '/pbl/admin/dashboard',
  children: [
    {
      path: 'dashboard',
      name: 'AdminDashboard',
      component: () => import('@pbl/admin/views/AdminDashboard.vue'),
      meta: { 
        title: '概览',
        roles: ['platform_admin', 'school_admin']
      }
    },
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
    // 学校管理员专用路由
    {
      path: 'classes',
      name: 'AdminClasses',
      component: () => import('@pbl/admin/views/AdminClasses.vue'),
      meta: { 
        title: '班级管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid',
      name: 'AdminClassDetail',
      component: () => import('@pbl/admin/views/AdminClassDetail.vue'),
      meta: {
        title: '班级详情',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/edit',
      name: 'AdminClassEdit',
      component: () => import('@pbl/admin/views/AdminClassEdit.vue'),
      meta: {
        title: '编辑班级',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/members',
      name: 'AdminClassMembers',
      component: () => import('@pbl/admin/views/AdminClassMembers.vue'),
      meta: {
        title: '成员管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/courses',
      name: 'AdminClassCourses',
      component: () => import('@pbl/admin/views/AdminClassCourses.vue'),
      meta: {
        title: '课程管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/groups',
      name: 'AdminClassGroups',
      component: () => import('@pbl/admin/views/AdminClassGroups.vue'),
      meta: {
        title: '小组管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/teachers',
      name: 'AdminClassTeachers',
      component: () => import('@pbl/admin/views/AdminClassTeachers.vue'),
      meta: {
        title: '教师管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/progress',
      name: 'AdminClassProgress',
      component: () => import('@pbl/admin/views/AdminClassProgress.vue'),
      meta: {
        title: '学习进度',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:classUuid/progress/units/:unitId',
      name: 'AdminClassUnitDetail',
      component: () => import('@pbl/admin/views/AdminClassUnitDetail.vue'),
      meta: {
        title: '单元详情',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/homework',
      name: 'AdminClassHomework',
      component: () => import('@pbl/admin/views/AdminClassHomework.vue'),
      meta: {
        title: '作业管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/homework/units/:unitId',
      name: 'AdminClassUnitHomework',
      component: () => import('@pbl/admin/views/AdminClassUnitHomework.vue'),
      meta: {
        title: '单元作业',
        roles: ['school_admin']
      }
    },
    {
      path: 'classes/:uuid/create-course',
      name: 'AdminClassCreateCourse',
      component: () => import('@pbl/admin/views/AdminClassCreateCourse.vue'),
      meta: {
        title: '创建课程',
        roles: ['school_admin']
      }
    },
    {
      path: 'teachers',
      name: 'TeacherManagement',
      component: () => import('@pbl/admin/views/TeacherManagement.vue'),
      meta: { 
        title: '教师管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'students',
      name: 'StudentManagement',
      component: () => import('@pbl/admin/views/StudentManagement.vue'),
      meta: { 
        title: '学生管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'available-templates',
      name: 'AvailableTemplates',
      component: () => import('@pbl/admin/views/AdminAvailableTemplates.vue'),
      meta: { 
        title: '课程模板库',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'template-detail/:uuid',
      name: 'TemplateDetail',
      component: () => import('@pbl/admin/views/AdminTemplateDetail.vue'),
      meta: {
        title: '模板详情',
        roles: ['platform_admin', 'school_admin', 'teacher']
      }
    },
    // 教师专用路由
    {
      path: 'my-classes',
      name: 'MyClasses',
      component: () => import('@pbl/admin/views/MyClasses.vue'),
      meta: { 
        title: '我的班级',
        roles: ['teacher']
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

// PBL渠道管理端路由
const channelManagementRoutes = {
  path: '/pbl/channel-mgmt',
  component: () => import('@/layouts/ChannelManagementLayout.vue'),
  meta: { requiresAuth: true, roles: ['channel_manager', 'platform_admin'] },
  redirect: '/pbl/channel-mgmt/partners',
  children: [
    {
      path: 'partners',
      name: 'ChannelPartners',
      component: () => import('@pbl/channel-mgmt/views/ChannelPartners.vue'),
      meta: { title: '渠道商管理' }
    },
    {
      path: 'partners/:partnerId',
      name: 'ChannelPartnerDetail',
      component: () => import('@pbl/channel-mgmt/views/ChannelPartnerDetail.vue'),
      meta: { title: '渠道商详情' }
    },
    {
      path: 'schools',
      name: 'SchoolManagement',
      component: () => import('@pbl/channel-mgmt/views/SchoolManagement.vue'),
      meta: { title: '学校管理' }
    },
    {
      path: 'assign-schools',
      name: 'AssignSchools',
      component: () => import('@pbl/channel-mgmt/views/AssignSchools.vue'),
      meta: { title: '学校分配' }
    },
    {
      path: 'statistics',
      name: 'ChannelStatistics',
      component: () => import('@pbl/channel-mgmt/views/ChannelStatistics.vue'),
      meta: { title: '渠道统计' }
    }
  ]
}

export default [studentRoutes, teacherRoutes, adminRoutes, channelRoutes, channelManagementRoutes]
