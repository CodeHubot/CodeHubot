/**
 * PBL系统路由配置 - 统一布局
 * 所有角色共用一个布局组件，根据角色动态显示不同的侧边栏菜单
 */

import { useAuthStore } from '@/stores/auth'

// PBL统一路由 - 所有角色共用一个布局
const unifiedPBLRoutes = {
  path: '/pbl',
  component: () => import('@/layouts/UnifiedPBLLayout.vue'),
  meta: { requiresAuth: true },
  redirect: () => {
    // 根据用户角色自动跳转到对应的首页
    const authStore = useAuthStore()
    if (authStore.isStudent) return '/pbl/student/courses'
    if (authStore.isTeacher) return '/pbl/school/dashboard'
    if (authStore.isSchoolAdmin) return '/pbl/school/dashboard'
    if (authStore.isChannelPartner) return '/pbl/channel/schools'
    if (authStore.isAdmin || authStore.isChannelManager) return '/pbl/admin/schools'
    return '/pbl/student/courses'
  },
  children: [
    // ==================== 学生路由 ====================
    {
      path: 'student/courses',
      name: 'StudentCourses',
      component: () => import('@pbl/student/views/MyCourses.vue'),
      meta: { title: '我的课程', roles: ['student'] }
    },
    {
      path: 'student/courses/:uuid',
      name: 'StudentCourseDetail',
      component: () => import('@pbl/student/views/CourseDetail.vue'),
      meta: { title: '课程详情', roles: ['student'] }
    },
    {
      path: 'student/units/:uuid',
      name: 'StudentUnitLearning',
      component: () => import('@pbl/student/views/UnitLearning.vue'),
      meta: { 
        title: '单元学习',
        hideSidebar: true,  // 隐藏侧边栏，全屏显示
        roles: ['student']
      }
    },
    {
      path: 'student/tasks',
      name: 'StudentTasks',
      component: () => import('@pbl/student/views/MyTasks.vue'),
      meta: { title: '我的任务', roles: ['student'] }
    },
    {
      path: 'student/projects',
      name: 'StudentProjects',
      component: () => import('@pbl/student/views/MyCourses.vue'),
      meta: { title: '我的项目', roles: ['student'] }
    },
    {
      path: 'student/portfolio',
      name: 'StudentPortfolio',
      component: () => import('@pbl/student/views/StudentPortfolio.vue'),
      meta: { title: '我的作品集', roles: ['student'] }
    },
    {
      path: 'student/learning-assistant',
      name: 'StudentLearningAssistant',
      component: () => import('@pbl/student/views/LearningAssistant.vue'),
      meta: { 
        title: 'AI学习助手',
        hideSidebar: false,  // 显示侧边栏导航
        roles: ['student']
      }
    },

    // ==================== 学校管理平台路由（教师和学校管理员） ====================
    {
      path: 'school/dashboard',
      name: 'SchoolDashboard',
      component: () => import('@pbl/school/views/SchoolDashboard.vue'),
      meta: { 
        title: '概览',
        roles: ['school_admin', 'teacher']
      }
    },
    // 教师专用功能
    {
      path: 'school/my-courses',
      name: 'SchoolMyCourses',
      component: () => import('@pbl/teacher/views/TeacherCourses.vue'),
      meta: { 
        title: '我的课程',
        roles: ['teacher']
      }
    },
    {
      path: 'school/grading',
      name: 'SchoolGrading',
      component: () => import('@pbl/teacher/views/TeacherTasks.vue'),
      meta: { 
        title: '作业批改',
        roles: ['teacher']
      }
    },
    {
      path: 'school/my-students',
      name: 'SchoolMyStudents',
      component: () => import('@pbl/teacher/views/TeacherStudents.vue'),
      meta: { 
        title: '我的学生',
        roles: ['teacher']
      }
    },
    // 学校管理员专用功能 - 用户管理
    {
      path: 'school/users',
      name: 'SchoolUserManagement',
      component: () => import('@pbl/school/views/SchoolUserManagement.vue'),
      meta: { 
        title: '用户管理',
        roles: ['school_admin']
      }
    },
    // 项目式课程管理（班级管理）
    {
      path: 'school/classes',
      name: 'SchoolClasses',
      component: () => import('@pbl/school/views/ClubClasses.vue'),
      meta: { 
        title: '项目式课程管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/classes/:uuid',
      name: 'SchoolClassDetail',
      component: () => import('@pbl/school/views/ClassDetail.vue'),
      meta: {
        title: '班级详情',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/classes/:uuid/edit',
      name: 'SchoolClassEdit',
      component: () => import('@pbl/admin/views/AdminClassEdit.vue'),
      meta: {
        title: '编辑班级',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/classes/:uuid/members',
      name: 'SchoolClassMembers',
      component: () => import('@pbl/admin/views/AdminClassMembers.vue'),
      meta: {
        title: '成员管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/classes/:uuid/groups',
      name: 'SchoolClassGroups',
      component: () => import('@pbl/admin/views/AdminClassGroups.vue'),
      meta: {
        title: '分组管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/classes/:uuid/teachers',
      name: 'SchoolClassTeachers',
      component: () => import('@pbl/admin/views/AdminClassTeachers.vue'),
      meta: {
        title: '教师管理',
        roles: ['school_admin']
      }
    },
    {
      path: 'school/classes/:uuid/courses',
      name: 'SchoolClassCourses',
      component: () => import('@pbl/admin/views/AdminClassCourses.vue'),
      meta: {
        title: '课程管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/classes/:uuid/progress',
      name: 'SchoolClassProgress',
      component: () => import('@pbl/admin/views/AdminClassProgress.vue'),
      meta: {
        title: '学习进度',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/classes/:uuid/progress/units/:unitId',
      name: 'SchoolClassUnitDetail',
      component: () => import('@pbl/admin/views/AdminClassUnitDetail.vue'),
      meta: {
        title: '单元详情',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/classes/:uuid/homework',
      name: 'SchoolClassHomework',
      component: () => import('@pbl/admin/views/AdminClassHomework.vue'),
      meta: {
        title: '作业管理',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/classes/:uuid/homework/units/:unitId',
      name: 'SchoolClassHomeworkUnitDetail',
      component: () => import('@pbl/admin/views/AdminClassUnitHomework.vue'),
      meta: {
        title: '单元作业',
        roles: ['school_admin', 'teacher']
      }
    },
    // 课程模板库
    {
      path: 'school/available-templates',
      name: 'SchoolAvailableTemplates',
      component: () => import('@pbl/school/views/AvailableTemplates.vue'),
      meta: { 
        title: '课程模板库',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/template-detail/:uuid',
      name: 'SchoolTemplateDetail',
      component: () => import('@pbl/school/views/TemplateDetail.vue'),
      meta: {
        title: '模板详情',
        roles: ['school_admin', 'teacher']
      }
    },
    {
      path: 'school/statistics',
      name: 'SchoolStatistics',
      component: () => import('@pbl/school/views/SchoolDashboard.vue'),
      meta: { 
        title: '数据统计',
        roles: ['school_admin']
      }
    },
    {
      path: 'school/learning-assistant',
      name: 'SchoolLearningAssistant',
      component: () => import('@pbl/school/views/LearningAssistantTeacher.vue'),
      meta: { 
        title: 'AI学习助手',
        roles: ['school_admin']
      }
    },

    // ==================== 平台管理路由（平台管理员和渠道管理员） ====================
    {
      path: 'admin/dashboard',
      name: 'AdminDashboard',
      component: () => import('@pbl/admin/views/AdminDashboardContent.vue'),
      meta: { 
        title: '管理控制台',
        roles: ['platform_admin', 'channel_manager']
      }
    },
    {
      path: 'admin/schools',
      name: 'AdminSchools',
      component: () => import('@pbl/admin/views/AdminSchools.vue'),
      meta: { 
        title: '学校管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/course-templates',
      name: 'CourseTemplates',
      component: () => import('@pbl/admin/views/CourseTemplates.vue'),
      meta: { 
        title: '课程模板管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/course-templates/:uuid',
      name: 'CourseTemplateDetail',
      component: () => import('@pbl/admin/views/CourseTemplateDetail.vue'),
      meta: { 
        title: '课程模板详情',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/template-permissions',
      name: 'TemplatePermissions',
      component: () => import('@pbl/admin/views/TemplatePermissions.vue'),
      meta: { 
        title: '模板授权管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/courses',
      name: 'AdminCourses',
      component: () => import('@pbl/admin/views/AdminCourses.vue'),
      meta: { 
        title: '课程管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/courses/:uuid',
      name: 'AdminCourseDetail',
      component: () => import('@pbl/admin/views/AdminCourseDetail.vue'),
      meta: { 
        title: '课程详情',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/units',
      name: 'AdminUnits',
      component: () => import('@pbl/admin/views/AdminUnits.vue'),
      meta: { 
        title: '学习单元',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/resources',
      name: 'AdminResources',
      component: () => import('@pbl/admin/views/AdminResources.vue'),
      meta: { 
        title: '资料管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/tasks',
      name: 'AdminTasks',
      component: () => import('@pbl/admin/views/AdminTasks.vue'),
      meta: { 
        title: '任务管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/users',
      name: 'AdminUsers',
      component: () => import('@pbl/admin/views/AdminUsersContent.vue'),
      meta: { 
        title: '用户管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/analytics',
      name: 'AdminAnalytics',
      component: () => import('@pbl/admin/views/AdminAnalyticsContent.vue'),
      meta: { 
        title: '数据统计',
        roles: ['platform_admin']
      }
    },
    // 班级管理相关路由（平台管理员）
    {
      path: 'admin/classes',
      name: 'AdminClasses',
      component: () => import('@pbl/admin/views/AdminClasses.vue'),
      meta: { 
        title: '班级管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid',
      name: 'AdminClassDetail',
      component: () => import('@pbl/admin/views/AdminClassDetail.vue'),
      meta: {
        title: '班级详情',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/edit',
      name: 'AdminClassEdit',
      component: () => import('@pbl/admin/views/AdminClassEdit.vue'),
      meta: {
        title: '编辑班级',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/members',
      name: 'AdminClassMembers',
      component: () => import('@pbl/admin/views/AdminClassMembers.vue'),
      meta: {
        title: '成员管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/groups',
      name: 'AdminClassGroups',
      component: () => import('@pbl/admin/views/AdminClassGroups.vue'),
      meta: {
        title: '分组管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/teachers',
      name: 'AdminClassTeachers',
      component: () => import('@pbl/admin/views/AdminClassTeachers.vue'),
      meta: {
        title: '教师管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/courses',
      name: 'AdminClassCourses',
      component: () => import('@pbl/admin/views/AdminClassCourses.vue'),
      meta: {
        title: '课程管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/create-course',
      name: 'AdminClassCreateCourse',
      component: () => import('@pbl/admin/views/AdminClassCreateCourse.vue'),
      meta: {
        title: '创建课程',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/progress',
      name: 'AdminClassProgress',
      component: () => import('@pbl/admin/views/AdminClassProgress.vue'),
      meta: {
        title: '学习进度',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/progress/units/:unitId',
      name: 'AdminClassUnitDetail',
      component: () => import('@pbl/admin/views/AdminClassUnitDetail.vue'),
      meta: {
        title: '单元详情',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/homework',
      name: 'AdminClassHomework',
      component: () => import('@pbl/admin/views/AdminClassHomework.vue'),
      meta: {
        title: '作业管理',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/classes/:uuid/homework/units/:unitId',
      name: 'AdminClassHomeworkUnitDetail',
      component: () => import('@pbl/admin/views/AdminClassUnitHomework.vue'),
      meta: {
        title: '单元作业',
        roles: ['platform_admin']
      }
    },
    // 模板相关路由（平台管理员）
    {
      path: 'admin/available-templates',
      name: 'AdminAvailableTemplates',
      component: () => import('@pbl/admin/views/AdminAvailableTemplates.vue'),
      meta: { 
        title: '可用模板',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/template-detail/:uuid',
      name: 'AdminTemplateDetail',
      component: () => import('@pbl/admin/views/AdminTemplateDetail.vue'),
      meta: {
        title: '模板详情',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/my-classes',
      name: 'AdminMyClasses',
      component: () => import('@pbl/admin/views/MyClasses.vue'),
      meta: { 
        title: '我的班级',
        roles: ['platform_admin']
      }
    },
    {
      path: 'admin/school-user-management',
      name: 'AdminSchoolUserManagement',
      component: () => import('@pbl/school/views/SchoolUserManagement.vue'),
      meta: { 
        title: '学校用户管理',
        roles: ['platform_admin']
      }
    },
    // 渠道管理功能（平台管理员和渠道管理员共享）
    {
      path: 'admin/channel/partners',
      name: 'AdminChannelPartners',
      component: () => import('@pbl/channel-mgmt/views/ChannelPartners.vue'),
      meta: { 
        title: '渠道商管理',
        roles: ['platform_admin', 'channel_manager']
      }
    },
    {
      path: 'admin/channel/partners/:partnerId',
      name: 'AdminChannelPartnerDetail',
      component: () => import('@pbl/channel-mgmt/views/ChannelPartnerDetail.vue'),
      meta: { 
        title: '渠道商详情',
        roles: ['platform_admin', 'channel_manager']
      }
    },
    {
      path: 'admin/channel/school-assignment',
      name: 'AdminSchoolAssignment',
      component: () => import('@pbl/channel-mgmt/views/AssignSchools.vue'),
      meta: { 
        title: '学校分配',
        roles: ['platform_admin', 'channel_manager']
      }
    },
    {
      path: 'admin/channel/statistics',
      name: 'AdminChannelStatistics',
      component: () => import('@pbl/channel-mgmt/views/ChannelStatistics.vue'),
      meta: { 
        title: '渠道统计',
        roles: ['platform_admin', 'channel_manager']
      }
    },

    // ==================== 渠道商路由 ====================
    {
      path: 'channel/schools',
      name: 'ChannelSchools',
      component: () => import('@pbl/channel/views/ChannelSchools.vue'),
      meta: { title: '合作学校', roles: ['channel_partner'] }
    },
    {
      path: 'channel/schools/:schoolId/courses',
      name: 'ChannelSchoolCourses',
      component: () => import('@pbl/channel/views/ChannelSchoolCourses.vue'),
      meta: { title: '学校课程', roles: ['channel_partner'] }
    },
    {
      path: 'channel/courses/:courseUuid',
      name: 'ChannelCourseDetail',
      component: () => import('@pbl/channel/views/ChannelCourseDetail.vue'),
      meta: { title: '课程详情', roles: ['channel_partner'] }
    }
  ]
}

// 导出统一的路由配置
export default [unifiedPBLRoutes]
