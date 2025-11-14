import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Calendar } from '@/components/ui/calendar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { format, differenceInDays, differenceInHours, differenceInMinutes, differenceInSeconds } from 'date-fns';
import { ru } from 'date-fns/locale';

type Screen = 'date' | 'name' | 'confirm' | 'main';

interface TimeRemaining {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

const Index = () => {
  const [screen, setScreen] = useState<Screen>('date');
  const [birthDate, setBirthDate] = useState<Date | undefined>();
  const [userName, setUserName] = useState('');
  const [showRealtime, setShowRealtime] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<TimeRemaining>({ days: 0, hours: 0, minutes: 0, seconds: 0 });

  const getNextBirthday = (birth: Date): Date => {
    const today = new Date();
    const thisYearBirthday = new Date(today.getFullYear(), birth.getMonth(), birth.getDate());
    
    if (thisYearBirthday < today) {
      return new Date(today.getFullYear() + 1, birth.getMonth(), birth.getDate());
    }
    return thisYearBirthday;
  };

  const calculateTimeRemaining = (): TimeRemaining => {
    if (!birthDate) return { days: 0, hours: 0, minutes: 0, seconds: 0 };
    
    const now = new Date();
    const nextBirthday = getNextBirthday(birthDate);
    
    const totalSeconds = Math.floor((nextBirthday.getTime() - now.getTime()) / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    
    return { days, hours, minutes, seconds };
  };

  useEffect(() => {
    if (showRealtime && birthDate) {
      const interval = setInterval(() => {
        setTimeRemaining(calculateTimeRemaining());
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [showRealtime, birthDate]);

  const handleDateSelect = (date: Date | undefined) => {
    setBirthDate(date);
    if (date) {
      setScreen('name');
    }
  };

  const handleNameSubmit = () => {
    if (userName.trim()) {
      setScreen('confirm');
    }
  };

  const handleConfirm = () => {
    setScreen('main');
  };

  const handleReset = () => {
    setBirthDate(undefined);
    setUserName('');
    setShowRealtime(false);
    setScreen('date');
  };

  const handleShowRealtime = () => {
    setTimeRemaining(calculateTimeRemaining());
    setShowRealtime(true);
  };

  const handleHideRealtime = () => {
    setShowRealtime(false);
  };

  const getDaysUntilBirthday = (): string => {
    if (!birthDate) return '';
    const nextBirthday = getNextBirthday(birthDate);
    const days = differenceInDays(nextBirthday, new Date());
    return `${days} ${days === 1 ? 'день' : days < 5 ? 'дня' : 'дней'}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0088cc]/10 to-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="shadow-xl border-primary/20 animate-fade-in">
          <CardHeader className="bg-primary text-primary-foreground rounded-t-xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Icon name="Cake" size={24} />
              </div>
              <div>
                <CardTitle className="text-xl">Обратный отсчёт</CardTitle>
                <CardDescription className="text-primary-foreground/80">
                  До дня рождения
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            {screen === 'date' && (
              <div className="space-y-4 animate-scale-in">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-medium text-foreground mb-2">Выберите дату рождения</h3>
                  <p className="text-sm text-muted-foreground">Это поможет отслеживать время до вашего праздника</p>
                </div>
                <Calendar
                  mode="single"
                  selected={birthDate}
                  onSelect={handleDateSelect}
                  locale={ru}
                  className="rounded-md border mx-auto"
                  disabled={(date) => date > new Date()}
                />
              </div>
            )}

            {screen === 'name' && (
              <div className="space-y-4 animate-scale-in">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-medium text-foreground mb-2">Как к вам обращаться?</h3>
                  <p className="text-sm text-muted-foreground">Введите ваше имя</p>
                </div>
                <Input
                  type="text"
                  placeholder="Ваше имя"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  className="text-center text-lg"
                  autoFocus
                  onKeyPress={(e) => e.key === 'Enter' && handleNameSubmit()}
                />
                <Button 
                  onClick={handleNameSubmit} 
                  className="w-full"
                  disabled={!userName.trim()}
                >
                  Продолжить
                  <Icon name="ArrowRight" size={18} className="ml-2" />
                </Button>
              </div>
            )}

            {screen === 'confirm' && (
              <div className="space-y-4 animate-scale-in">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-medium text-foreground mb-2">Подтверждение</h3>
                  <p className="text-sm text-muted-foreground">Проверьте введённые данные</p>
                </div>
                <div className="bg-secondary/50 p-4 rounded-lg space-y-3">
                  <div className="flex items-center gap-3">
                    <Icon name="User" size={20} className="text-primary" />
                    <div>
                      <p className="text-xs text-muted-foreground">Имя</p>
                      <p className="font-medium">{userName}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Icon name="Calendar" size={20} className="text-primary" />
                    <div>
                      <p className="text-xs text-muted-foreground">Дата рождения</p>
                      <p className="font-medium">
                        {birthDate && format(birthDate, 'd MMMM yyyy', { locale: ru })}
                      </p>
                    </div>
                  </div>
                </div>
                <Button onClick={handleConfirm} className="w-full">
                  <Icon name="Check" size={18} className="mr-2" />
                  Готово
                </Button>
              </div>
            )}

            {screen === 'main' && (
              <div className="space-y-4 animate-scale-in">
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-medium text-foreground mb-1">Привет, {userName}! 👋</h3>
                  <p className="text-sm text-muted-foreground">
                    День рождения: {birthDate && format(birthDate, 'd MMMM', { locale: ru })}
                  </p>
                </div>

                {!showRealtime && (
                  <div className="bg-gradient-to-br from-primary/10 to-primary/5 p-6 rounded-xl text-center border border-primary/20">
                    <Icon name="Gift" size={48} className="mx-auto mb-3 text-primary" />
                    <p className="text-sm text-muted-foreground mb-1">До вашего дня рождения</p>
                    <p className="text-4xl font-bold text-primary">{getDaysUntilBirthday()}</p>
                  </div>
                )}

                {showRealtime && (
                  <div className="bg-gradient-to-br from-primary/10 to-primary/5 p-6 rounded-xl text-center border border-primary/20">
                    <div className="flex items-center justify-center gap-2 mb-4">
                      <Icon name="Timer" size={24} className="text-primary animate-pulse" />
                      <p className="text-sm font-medium text-muted-foreground">РЕАЛЬНОЕ ВРЕМЯ</p>
                    </div>
                    <div className="grid grid-cols-4 gap-2">
                      <div className="bg-white/50 p-3 rounded-lg">
                        <p className="text-2xl font-bold text-primary">{timeRemaining.days}</p>
                        <p className="text-xs text-muted-foreground">дней</p>
                      </div>
                      <div className="bg-white/50 p-3 rounded-lg">
                        <p className="text-2xl font-bold text-primary">{timeRemaining.hours}</p>
                        <p className="text-xs text-muted-foreground">часов</p>
                      </div>
                      <div className="bg-white/50 p-3 rounded-lg">
                        <p className="text-2xl font-bold text-primary">{timeRemaining.minutes}</p>
                        <p className="text-xs text-muted-foreground">минут</p>
                      </div>
                      <div className="bg-white/50 p-3 rounded-lg">
                        <p className="text-2xl font-bold text-primary">{timeRemaining.seconds}</p>
                        <p className="text-xs text-muted-foreground">секунд</p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="space-y-2 pt-2">
                  {!showRealtime ? (
                    <Button onClick={handleShowRealtime} className="w-full" variant="default">
                      <Icon name="Timer" size={18} className="mr-2" />
                      Сколько до дня рождения в реальном времени?
                    </Button>
                  ) : (
                    <Button onClick={handleHideRealtime} className="w-full" variant="outline">
                      <Icon name="X" size={18} className="mr-2" />
                      Скрыть реальное время
                    </Button>
                  )}
                  <Button onClick={handleReset} className="w-full" variant="outline">
                    <Icon name="RotateCcw" size={18} className="mr-2" />
                    Сбросить дату дня рождения
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Index;
