import React from 'react';
import { Button, Result } from 'antd';
import { useNavigate } from 'react-router-dom';
import { ToolOutlined } from '@ant-design/icons';
import styles from './styles.module.css';

export default function UnderConstruction() {
  const navigate = useNavigate();

  return (
    <div className={styles.container}>
      <Result
        icon={<ToolOutlined className={styles.icon} />}
        title="功能建设中"
        subTitle="该功能正在紧锣密鼓地开发中，敬请期待！"
        extra={
          <Button
            type="primary"
            onClick={() => navigate('/experiments')}
            className={styles.backButton}
          >
            返回实验列表
          </Button>
        }
      />
    </div>
  );
}
