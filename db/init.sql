-- ============================================================
-- 科目一考试系统 初始化种子数据 (幂等，可重复执行)
-- 角色已由 schema.sql 初始化；本脚本补充：默认分类/权限/角色-权限授权
-- ============================================================
USE driving_subject1;

-- 1) 默认题目分类（不存在才插入）
INSERT INTO question_category (cat_name, sort)
SELECT '科目一全真题库', 0
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM question_category WHERE cat_name = '科目一全真题库');

-- 2) 权限种子（perm_code 唯一，IGNORE 幂等）
INSERT IGNORE INTO sys_permission (perm_name, perm_code) VALUES
('用户查看','user:list'),
('用户新增','user:add'),
('用户修改','user:update'),
('角色查看','role:list'),
('角色授权','role:assign'),
('分类维护','category:manage'),
('题目维护','question:manage'),
('题目导出','question:export'),
('试卷维护','paper:manage'),
('随机组卷','paper:random'),
('成绩统计','stat:view'),
('考生功能','student:use');

-- 3) 角色-权限授权（幂等：不存在才插入）
-- 系统管理员：全部权限
INSERT IGNORE INTO sys_role_perm (role_id, perm_id)
SELECT r.role_id, p.perm_id
FROM sys_role r JOIN sys_permission p ON 1=1
WHERE r.role_code = 'SYS_ADMIN'
  AND NOT EXISTS (
    SELECT 1 FROM sys_role_perm rp WHERE rp.role_id = r.role_id AND rp.perm_id = p.perm_id
  );

-- 题库管理员：分类/题库/导出/试卷/组卷，不可操作用户与角色
INSERT IGNORE INTO sys_role_perm (role_id, perm_id)
SELECT r.role_id, p.perm_id
FROM sys_role r JOIN sys_permission p ON p.perm_code IN (
    'category:manage','question:manage','question:export','paper:manage','paper:random'
)
WHERE r.role_code = 'QUESTION_ADMIN'
  AND NOT EXISTS (
    SELECT 1 FROM sys_role_perm rp WHERE rp.role_id = r.role_id AND rp.perm_id = p.perm_id
  );

-- 考生：仅考生功能
INSERT IGNORE INTO sys_role_perm (role_id, perm_id)
SELECT r.role_id, p.perm_id
FROM sys_role r JOIN sys_permission p ON p.perm_code IN ('student:use')
WHERE r.role_code = 'STUDENT'
  AND NOT EXISTS (
    SELECT 1 FROM sys_role_perm rp WHERE rp.role_id = r.role_id AND rp.perm_id = p.perm_id
  );
