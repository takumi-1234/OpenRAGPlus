// api-go/internal/config/config.go

package config

import (
	"github.com/spf13/viper"
)

type Config struct {
	DBSource      string `mapstructure:"DB_SOURCE"`
	ServerAddress string `mapstructure:"SERVER_ADDRESS"`
	JWTSecretKey  string `mapstructure:"JWT_SECRET_KEY"`
}

func LoadConfig(path string) (config Config, err error) {
	viper.AddConfigPath(path)
	viper.SetConfigName(".env")
	viper.SetConfigType("env")

	viper.AutomaticEnv()

	err = viper.ReadInConfig()
	if err != nil {
		// .envファイルがなくても環境変数から読めるようにエラーを無視するケースもある
		// ここではエラーとして扱う
		return
	}

	err = viper.Unmarshal(&config)
	return
}
