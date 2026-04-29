import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import UnderConstruction from './UnderConstruction';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderComponent = () => {
  return render(
    <BrowserRouter>
      <UnderConstruction />
    </BrowserRouter>
  );
};

describe('UnderConstruction', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it('should render the under construction message', () => {
    renderComponent();

    expect(screen.getByText('功能建设中')).toBeInTheDocument();
    expect(screen.getByText('该功能正在紧锣密鼓地开发中，敬请期待！')).toBeInTheDocument();
  });

  it('should render the return button', () => {
    renderComponent();

    const returnButton = screen.getByRole('button', { name: '返回实验列表' });
    expect(returnButton).toBeInTheDocument();
  });

  it('should navigate to experiments when return button is clicked', async () => {
    const user = userEvent.setup();
    renderComponent();

    const returnButton = screen.getByRole('button', { name: '返回实验列表' });
    await user.click(returnButton);

    expect(mockNavigate).toHaveBeenCalledWith('/experiments');
  });
});
