"""
전역 설정 관리
- 주문 모드 (실전/시뮬레이션)
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE = '.data/global_config.json'


class GlobalConfig:
    """전역 설정 관리"""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """설정 파일 로드"""
        if not os.path.exists(CONFIG_FILE):
            return self._get_default_config()

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """기본 설정 (TRADE_MODE 환경변수 우선)"""
        import os
        trade_mode = os.getenv('TRADE_MODE', 'mock')  # 'real' or 'mock'
        order_mode = 'real' if trade_mode == 'real' else 'simulation'
        return {
            'order_mode': order_mode,
            'updated_at': None
        }

    def _save_config(self):
        """설정 파일 저장"""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")

    def get_order_mode(self) -> str:
        """주문 모드 조회"""
        return self.config.get('order_mode', 'simulation')

    def set_order_mode(self, mode: str) -> bool:
        """
        주문 모드 설정 (global_config.json + .env TRADE_MODE 동시 업데이트)

        Args:
            mode: 'simulation' or 'real'

        Returns:
            bool: 성공 여부
        """
        if mode not in ['simulation', 'real']:
            logger.error(f"잘못된 주문 모드: {mode}")
            return False

        from datetime import datetime
        self.config['order_mode'] = mode
        self.config['updated_at'] = datetime.now().isoformat()
        self._save_config()

        # .env 파일의 TRADE_MODE도 함께 업데이트
        self._update_env_trade_mode(mode)

        logger.info(f"주문 모드 변경: {mode}")
        return True

    def _update_env_trade_mode(self, mode: str):
        """
        .env 파일의 TRADE_MODE 업데이트

        Args:
            mode: 'simulation' or 'real'
        """
        try:
            env_path = '.env'
            if not os.path.exists(env_path):
                logger.warning(f".env 파일이 없습니다: {env_path}")
                return

            # .env 파일 읽기
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # TRADE_MODE 찾아서 업데이트
            trade_mode_value = 'real' if mode == 'real' else 'mock'
            updated = False
            new_lines = []

            for line in lines:
                if line.strip().startswith('TRADE_MODE='):
                    new_lines.append(f'TRADE_MODE={trade_mode_value}\n')
                    updated = True
                else:
                    new_lines.append(line)

            # TRADE_MODE가 없으면 추가
            if not updated:
                new_lines.append(f'\n# 거래 모드 (auto-updated by global_config)\nTRADE_MODE={trade_mode_value}\n')

            # 파일 쓰기
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            logger.info(f".env TRADE_MODE 업데이트: {trade_mode_value}")

        except Exception as e:
            logger.error(f".env 파일 업데이트 실패: {e}")

    def is_simulation_mode(self) -> bool:
        """시뮬레이션 모드인지 확인"""
        return self.get_order_mode() == 'simulation'

    def get_config(self) -> dict:
        """전체 설정 조회"""
        return self.config.copy()


# 전역 인스턴스
_global_config = None


def get_global_config() -> GlobalConfig:
    """전역 설정 인스턴스 조회"""
    global _global_config
    if _global_config is None:
        _global_config = GlobalConfig()
    return _global_config
